import crypto from 'crypto';
import { sessionStore } from './session-store.js';
import { ChatMessage, CreateSessionOptions, LobbyMessage, LobbySnapshot } from './types.js';

const MAX_CHAT_MESSAGES = 200;

class LobbyStore {
  private messages: ChatMessage[] = [];

  getSnapshot(): LobbySnapshot {
    const roomSummaries = sessionStore.listSessions().map((session) => sessionStore.summarize(session));

    const resolvedMessages: LobbyMessage[] = this.messages.map((message) => ({
      ...message,
      sessionSummary: message.sessionId
        ? roomSummaries.find((summary) => summary.sessionId === message.sessionId)
        : undefined,
    }));

    return {
      messages: resolvedMessages,
      rooms: roomSummaries,
    };
  }

  postUserMessage(author: string, body: string, sessionId?: string): LobbyMessage {
    const message = this.appendMessage({
      id: crypto.randomUUID(),
      author,
      body,
      timestamp: new Date().toISOString(),
      type: 'user',
      sessionId,
    });

    return message;
  }

  postSystemMessage(body: string, sessionId?: string): LobbyMessage {
    return this.appendMessage({
      id: crypto.randomUUID(),
      author: 'system',
      body,
      timestamp: new Date().toISOString(),
      type: 'system',
      sessionId,
    });
  }

  createRoom(options: CreateSessionOptions) {
    const session = sessionStore.createSession(options);

    const summary = sessionStore.summarize(session);
    const joinable = summary.passwordProtected ? 'locked lobby' : 'open lobby';
    this.postSystemMessage(
      `${summary.ownerName} opened a ${summary.difficulty} ${joinable} (${summary.playerCount}/${summary.maxPlayers}).`,
      session.id,
    );

    return session;
  }

  private appendMessage(message: ChatMessage): LobbyMessage {
    this.messages.push(message);

    if (this.messages.length > MAX_CHAT_MESSAGES) {
      this.messages.splice(0, this.messages.length - MAX_CHAT_MESSAGES);
    }

    const snapshot = sessionStore.listSessions().map((session) => sessionStore.summarize(session));
    return {
      ...message,
      sessionSummary: message.sessionId
        ? snapshot.find((summary) => summary.sessionId === message.sessionId)
        : undefined,
    };
  }
}

export const lobbyStore = new LobbyStore();
