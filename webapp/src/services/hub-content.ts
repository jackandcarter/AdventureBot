import { RowDataPacket } from 'mysql2/promise';
import { HttpError } from '../errors/http-error.js';
import { pool } from '../db/pool.js';

export type HubEmbedType = 'main' | 'tutorial' | 'news';

interface HubEmbedRow extends RowDataPacket {
  embed_type: HubEmbedType;
  title: string | null;
  description: string | null;
  image_url: string | null;
  text_field: string | null;
  step_order: number | null;
  created_at: string;
}

export interface HubEmbed {
  type: HubEmbedType;
  title: string | null;
  description: string | null;
  imageUrl: string | null;
  text: string | null;
  stepOrder: number | null;
  createdAt: string;
}

const mapEmbedRow = (row: HubEmbedRow): HubEmbed => ({
  type: row.embed_type,
  title: row.title,
  description: row.description,
  imageUrl: row.image_url,
  text: row.text_field,
  stepOrder: row.step_order,
  createdAt: row.created_at,
});

export const fetchMainHubEmbed = async (): Promise<HubEmbed | null> => {
  const [rows] = await pool.query<HubEmbedRow[]>(
    `SELECT embed_type, title, description, image_url, text_field, step_order, created_at
     FROM hub_embeds
     WHERE embed_type = 'main'
     ORDER BY step_order ASC
     LIMIT 1`,
  );

  return rows[0] ? mapEmbedRow(rows[0]) : null;
};

export const fetchTutorialEmbeds = async (): Promise<HubEmbed[]> => {
  const [rows] = await pool.query<HubEmbedRow[]>(
    `SELECT embed_type, title, description, image_url, text_field, step_order, created_at
     FROM hub_embeds
     WHERE embed_type = 'tutorial'
     ORDER BY step_order ASC, created_at ASC`,
  );

  return rows.map(mapEmbedRow);
};

export const fetchTutorialPage = async (
  page: number,
): Promise<{ page: number; totalPages: number; embed: HubEmbed }> => {
  const steps = await fetchTutorialEmbeds();

  if (!steps.length) {
    throw new HttpError(404, 'No tutorial pages are available yet');
  }

  const totalPages = steps.length;
  const index = (page - 1) % totalPages;
  const embed = steps[index];

  return { page: index + 1, totalPages, embed };
};

export type HighScoreSort =
  | 'score_value'
  | 'enemies_defeated'
  | 'bosses_defeated'
  | 'gil'
  | 'player_level'
  | 'rooms_visited';

interface HighScoreRow extends RowDataPacket {
  player_name: string;
  player_class: string | null;
  score_value: number;
  enemies_defeated: number;
  bosses_defeated: number;
  rooms_visited: number;
  gil: number;
  player_level: number;
  difficulty: string | null;
  completed_at: string;
}

export interface HighScoreEntry {
  playerName: string;
  playerClass: string | null;
  scoreValue: number;
  enemiesDefeated: number;
  bossesDefeated: number;
  roomsVisited: number;
  gil: number;
  playerLevel: number;
  difficulty: string | null;
  completedAt: string;
}

export const fetchHighScores = async (
  sortBy: HighScoreSort,
  limit = 20,
): Promise<HighScoreEntry[]> => {
  const [rows] = await pool.query<HighScoreRow[]>(
    `SELECT player_name, player_class, score_value, enemies_defeated, bosses_defeated, rooms_visited, gil, player_level, difficulty, completed_at
     FROM high_scores
     ORDER BY ${sortBy} DESC, completed_at DESC
     LIMIT ?`,
    [limit],
  );

  return rows.map((row) => ({
    playerName: row.player_name,
    playerClass: row.player_class,
    scoreValue: row.score_value,
    enemiesDefeated: row.enemies_defeated,
    bossesDefeated: row.bosses_defeated,
    roomsVisited: row.rooms_visited,
    gil: row.gil,
    playerLevel: row.player_level,
    difficulty: row.difficulty,
    completedAt: row.completed_at,
  }));
};

