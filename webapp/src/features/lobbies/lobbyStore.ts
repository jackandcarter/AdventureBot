import { randomUUID } from 'crypto';
import {
  CreateLobbyInput,
  JoinLobbyInput,
  LeaveLobbyInput,
  Lobby,
  LobbyPlayer,
  LobbyVisibility,
  SetReadyInput,
  StartLobbyInput,
} from './types.js';

const generateInviteCode = () => Math.random().toString(36).substring(2, 8).toUpperCase();

const DEFAULT_MAX_PLAYERS = 6;

export class LobbyStore {
  private lobbies = new Map<string, Lobby>();

  createLobby(input: CreateLobbyInput): Lobby {
    const now = new Date();
    const visibility: LobbyVisibility = input.visibility ?? 'public';
    const inviteCode = visibility === 'invite' ? generateInviteCode() : undefined;
    const lobby: Lobby = {
      id: randomUUID(),
      name: input.name?.trim() || 'New Lobby',
      ownerId: input.ownerId,
      visibility,
      status: 'open',
      inviteCode,
      createdAt: now,
      updatedAt: now,
      maxPlayers: Math.min(input.maxPlayers ?? DEFAULT_MAX_PLAYERS, DEFAULT_MAX_PLAYERS),
      players: [
        {
          id: input.ownerId,
          displayName: 'Owner',
          ready: false,
          joinedAt: now,
        },
      ],
    };

    this.lobbies.set(lobby.id, lobby);
    return lobby;
  }

  listPublicLobbies(): Lobby[] {
    return Array.from(this.lobbies.values()).filter((lobby) => lobby.visibility === 'public');
  }

  getLobby(lobbyId: string): Lobby | undefined {
    return this.lobbies.get(lobbyId);
  }

  joinLobby(input: JoinLobbyInput): Lobby {
    const lobby = this.getLobby(input.lobbyId);
    if (!lobby) {
      throw new Error('Lobby not found');
    }

    if (lobby.status !== 'open') {
      throw new Error('Lobby is not accepting players');
    }

    if (lobby.players.some((player) => player.id === input.playerId)) {
      return lobby;
    }

    if (lobby.players.length >= lobby.maxPlayers) {
      throw new Error('Lobby is full');
    }

    const player: LobbyPlayer = {
      id: input.playerId,
      displayName: input.displayName || 'Player',
      ready: false,
      joinedAt: new Date(),
    };

    lobby.players = [...lobby.players, player];
    lobby.updatedAt = new Date();
    return lobby;
  }

  leaveLobby(input: LeaveLobbyInput): Lobby | undefined {
    const lobby = this.getLobby(input.lobbyId);
    if (!lobby) {
      throw new Error('Lobby not found');
    }

    lobby.players = lobby.players.filter((player) => player.id !== input.playerId);

    if (lobby.players.length === 0) {
      this.lobbies.delete(lobby.id);
      return undefined;
    }

    if (lobby.ownerId === input.playerId) {
      lobby.ownerId = lobby.players[0].id;
    }

    lobby.status = lobby.status === 'starting' ? 'open' : lobby.status;
    lobby.updatedAt = new Date();
    return lobby;
  }

  setReady(input: SetReadyInput): Lobby {
    const lobby = this.getLobby(input.lobbyId);
    if (!lobby) {
      throw new Error('Lobby not found');
    }

    lobby.players = lobby.players.map((player) =>
      player.id === input.playerId ? { ...player, ready: input.ready } : player,
    );
    lobby.updatedAt = new Date();
    return lobby;
  }

  startLobby(input: StartLobbyInput): Lobby {
    const lobby = this.getLobby(input.lobbyId);
    if (!lobby) {
      throw new Error('Lobby not found');
    }

    if (lobby.ownerId !== input.playerId) {
      throw new Error('Only the lobby owner can start the game');
    }

    if (lobby.players.length === 0) {
      throw new Error('Lobby has no players');
    }

    const everyoneReady = lobby.players.every((player) => player.ready);
    if (!everyoneReady) {
      throw new Error('All players must be ready to start');
    }

    lobby.status = 'starting';
    lobby.updatedAt = new Date();
    return lobby;
  }
}

export const lobbyStore = new LobbyStore();
