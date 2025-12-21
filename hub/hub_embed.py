import discord
import json
import logging
from models.database import Database  # Centralized database helper

logger = logging.getLogger("HubEmbed")
logger.setLevel(logging.DEBUG)

HIGH_SCORE_SORT_OPTIONS = {
    "enemies_defeated": {
        "label": "Enemies Defeated",
        "description": "Total enemies defeated in a session.",
        "direction": "DESC",
    },
    "rooms_visited": {
        "label": "Rooms Explored",
        "description": "Total rooms visited in a session.",
        "direction": "DESC",
    },
    "items_found": {
        "label": "Items Found",
        "description": "Total items found in a session.",
        "direction": "DESC",
    },
    "player_level": {
        "label": "Highest Level",
        "description": "Highest player level achieved in a session.",
        "direction": "DESC",
    },
    "gil": {
        "label": "Gil Earned",
        "description": "Total gil collected during a session.",
        "direction": "DESC",
    },
    "play_time": {
        "label": "Fastest Clear",
        "description": "Shortest session completion time.",
        "direction": "ASC",
    },
}

def _format_play_time(play_time: int | None) -> str:
    if play_time is None:
        return "N/A"
    if play_time < 60:
        return f"{play_time}s"
    minutes, seconds = divmod(play_time, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"

def get_main_hub_embed():
    """
    Retrieves the main hub embed configuration from the 'hub_embeds' table
    where embed_type is 'main'. If not found, returns a fallback embed.
    """
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT * FROM hub_embeds WHERE embed_type = 'main' LIMIT 1"
        cursor.execute(sql)
        result = cursor.fetchone()
        if result:
            embed = discord.Embed(
                title=result.get("title", "Welcome to AdventureBot!"),
                description=result.get("description", "Select an option below:"),
                color=discord.Color.blue()
            )
            if result.get("image_url"):
                embed.set_image(url=result["image_url"])
            if result.get("text_field"):
                embed.add_field(name="**__News__**", value=result["text_field"], inline=False)
            return embed
        else:
            embed = discord.Embed(
                title="Welcome to AdventureBot!",
                description="Select an option below to start or join a game.",
                color=discord.Color.blue()
            )
            embed.set_image(url="https://yourdomain.com/path/to/large_logo.jpg")
            embed.add_field(name="**__News__**", value="Game Hub configured via backend.", inline=False)
            return embed
    except Exception as e:
        logger.error("Error retrieving main hub embed: %s", e, exc_info=True)
        return discord.Embed(
            title="Welcome to AdventureBot!",
            description="Select an option below to start or join a game.",
            color=discord.Color.blue()
        )
    finally:
        cursor.close()
        conn.close()

def get_tutorial_embed(page: int):
    """
    Retrieves the tutorial embed for the specified page.
    Queries the 'hub_embeds' table for entries with embed_type 'tutorial'
    ordered by step_order and returns the embed for the given page.
    """
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT * FROM hub_embeds WHERE embed_type = 'tutorial' ORDER BY step_order ASC"
        cursor.execute(sql)
        steps = cursor.fetchall()
        total_pages = len(steps)
        if total_pages == 0:
            embed = discord.Embed(
                title=f"Tutorial - Step {page}",
                description="No tutorial content found in the backend.",
                color=discord.Color.purple()
            )
            return embed

        index = (page - 1) % total_pages
        step = steps[index]
        embed = discord.Embed(
            title=step.get("title", f"Tutorial - Step {page}"),
            description=step.get("description", "Learn how to play the game here."),
            color=discord.Color.purple()
        )
        if step.get("image_url"):
            embed.set_image(url=step["image_url"])
        embed.set_footer(text="Use the Next and Previous buttons to navigate, or Close to exit.")
        return embed
    except Exception as e:
        logger.error("Error retrieving tutorial embed: %s", e, exc_info=True)
        return discord.Embed(
            title=f"Tutorial - Step {page}",
            description="An error occurred while loading the tutorial.",
            color=discord.Color.purple()
        )
    finally:
        cursor.close()
        conn.close()

def get_tutorial_page_count() -> int:
    """
    Retrieves the number of tutorial pages from the 'hub_embeds' table.
    """
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        sql = "SELECT COUNT(*) FROM hub_embeds WHERE embed_type = 'tutorial'"
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        logger.error("Error retrieving tutorial page count: %s", e, exc_info=True)
        return 0
    finally:
        cursor.close()
        conn.close()

def get_high_scores_embed(high_scores_data):
    """
    Constructs an embed to display high scores.
    Expects high_scores_data as a list of dictionaries containing score info.
    """
    return get_high_scores_embed_for_sort(high_scores_data, "enemies_defeated")

def get_high_scores_embed_for_sort(high_scores_data, sort_key: str):
    """
    Constructs an embed to display high scores for a given sort key.
    Expects high_scores_data as a list of dictionaries containing score info.
    """
    sort_meta = HIGH_SCORE_SORT_OPTIONS.get(sort_key, HIGH_SCORE_SORT_OPTIONS["enemies_defeated"])
    embed = discord.Embed(
        title="High Scores",
        description=(
            "Select a sorting option from the dropdown to view the top 20 "
            "session records for that category."
        ),
        color=discord.Color.gold()
    )
    embed.add_field(
        name="Current Sort",
        value=f"**{sort_meta['label']}** — {sort_meta['description']}",
        inline=False
    )
    options_text = "\n".join(
        f"• **{meta['label']}** — {meta['description']}"
        for meta in HIGH_SCORE_SORT_OPTIONS.values()
    )
    embed.add_field(name="Sorting Options", value=options_text, inline=False)

    if not high_scores_data:
        embed.add_field(
            name="No scores available",
            value="Be the first to set a record!",
            inline=False
        )
        return embed

    lines = []
    for idx, entry in enumerate(high_scores_data, start=1):
        player_name = entry.get("player_name", "Unknown")
        player_class = entry.get("player_class", "Unknown Class")
        difficulty = entry.get("difficulty", "Unknown Difficulty")
        enemies_defeated = entry.get("enemies_defeated", 0)
        rooms_visited = entry.get("rooms_visited", 0)
        items_found = entry.get("items_found", 0)
        player_level = entry.get("player_level", 0)
        gil = entry.get("gil", 0)
        play_time = _format_play_time(entry.get("play_time"))
        lines.append(
            (
                f"**{idx}. {player_name}** "
                f"({player_class} · {difficulty})\n"
                f"Enemies: {enemies_defeated} | "
                f"Rooms: {rooms_visited} | "
                f"Items: {items_found}\n"
                f"Level: {player_level} | "
                f"Gil: {gil} | "
                f"Time: {play_time}"
            )
        )

    embed.add_field(
        name="Top 20 Sessions",
        value="\n\n".join(lines),
        inline=False
    )
    return embed
