import discord
import json
import logging
from models.database import Database  # Centralized database helper

logger = logging.getLogger("HubEmbed")
logger.setLevel(logging.DEBUG)

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
        embed.set_footer(text="Use the Next and Previous buttons to navigate, or Back to return to the main menu.")
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
    embed = discord.Embed(
        title="High Scores",
        description="Top players and session stats:",
        color=discord.Color.gold()
    )
    if not high_scores_data:
        embed.add_field(name="No scores available", value="Be the first to set a record!", inline=False)
    else:
        for entry in high_scores_data:
            embed.add_field(
                name=f"{entry.get('player_name', 'Unknown')} ({entry.get('player_class', 'N/A')})",
                value=f"Rooms: {entry.get('rooms', 'N/A')}\nEnemies: {entry.get('enemies', 'N/A')}\nGil: {entry.get('gil', 'N/A')}",
                inline=False
            )
    embed.set_footer(text="Press 'Back' to return to the main menu.")
    return embed
