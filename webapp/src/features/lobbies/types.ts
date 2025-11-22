export type LobbyVisibility = 'public' | 'private' | 'invite';

export type LobbyStatus = 'open' | 'starting' | 'closed';

export interface LobbyPlayer {
  id: string;
  displayName: string;
  ready: boolean;
  joinedAt: Date;
}

export interface Lobby {
  id: string;
  name: string;
  ownerId: string;
  visibility: LobbyVisibility;
  status: LobbyStatus;
  inviteCode?: string;
  createdAt: Date;
  updatedAt: Date;
  maxPlayers: number;
  players: LobbyPlayer[];
}

export interface CreateLobbyInput {
  ownerId: string;
  name?: string;
  visibility?: LobbyVisibility;
  maxPlayers?: number;
}

export interface JoinLobbyInput {
  lobbyId: string;
  playerId: string;
  displayName: string;
}

export interface SetReadyInput {
  lobbyId: string;
  playerId: string;
  ready: boolean;
}

export interface LeaveLobbyInput {
  lobbyId: string;
  playerId: string;
}

export interface StartLobbyInput {
  lobbyId: string;
  playerId: string;
}
