const statusEl = document.querySelector('#status');
const roomsEl = document.querySelector('#rooms');
const lobbyFeedEl = document.querySelector('#chat');
const sessionViewEl = document.querySelector('#session');
const createRoomResultEl = document.querySelector('#create-room-result');
const joinResultEl = document.querySelector('#join-result');
const difficultyCardsEl = document.querySelector('#difficulty-cards');
const legendEl = document.querySelector('#legend');
const startResultEl = document.querySelector('#start-result');
const statRoomsEl = document.querySelector('#stat-rooms');
const statPlayersEl = document.querySelector('#stat-players');
const statWaitingEl = document.querySelector('#stat-waiting');
const onlineUsersEl = document.querySelector('#online-users');

let difficultyDefinitions = [];
let currentUser = null;

const api = async (path, options = {}) => {
  const { headers, ...rest } = options;
  const response = await fetch(`/api${path}`, {
    credentials: 'include',
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(headers || {}),
    },
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.message || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload;
};

const ensureAuthenticated = async () => {
  try {
    const { user } = await api('/auth/me');
    currentUser = user;
    if (statusEl) {
      statusEl.textContent = `Signed in as ${user.displayName}`;
    }
  } catch (error) {
    window.location.href = '/login';
    throw error;
  }
};

const roomLegend = [
  { type: 'entrance', label: 'Entrance', detail: 'Starting point for the party.' },
  { type: 'safe', label: 'Safe', detail: 'Quiet corridors with no threats.' },
  { type: 'monster', label: 'Monster', detail: 'Triggers combat using difficulty-scaled stats.' },
  { type: 'boss', label: 'Boss', detail: 'Placed on the final floor as a capstone fight.' },
  { type: 'item', label: 'Treasure', detail: 'Contains loot such as potions or keys.' },
  { type: 'shop', label: 'Shop', detail: 'A wandering merchant appears.' },
  { type: 'locked', label: 'Locked', detail: 'Requires a key obtained from treasure rooms.' },
  { type: 'trap', label: 'Trap', detail: 'Deals damage on entry.' },
  { type: 'illusion', label: 'Illusion', detail: 'Flavor rooms highlighting hidden passages.' },
  { type: 'staircase_down', label: 'Stairs Down', detail: 'Descend to the next floor once cleared.' },
  { type: 'staircase_up', label: 'Stairs Up', detail: 'Return toward safety.' },
  { type: 'exit', label: 'Exit', detail: 'A future hook for leaving early.' },
];

const formatDifficulty = (key) => difficultyDefinitions.find((d) => d.key === key)?.name || key;

const renderDifficultyCards = () => {
  if (!difficultyCardsEl) return;
  difficultyCardsEl.innerHTML = '';

  difficultyDefinitions.forEach((def) => {
    const card = document.createElement('div');
    card.className = 'card';

    card.innerHTML = `
      <strong>${def.name}</strong>
      <div class="muted">${def.width}×${def.height} grid • ${def.minFloors}-${def.maxFloors} floors</div>
      <div class="muted">Enemy chance ${Math.round(def.enemyChance * 100)}% · NPC slots ${def.npcCount}</div>
      <div class="muted">Basement chance ${Math.round(def.basementChance * 100)}% (${def.basementMinRooms}-${def.basementMaxRooms} rooms)</div>
    `;

    difficultyCardsEl.appendChild(card);
  });
};

const renderLegend = () => {
  if (!legendEl) return;
  legendEl.innerHTML = '';
  roomLegend.forEach((entry) => {
    const node = document.createElement('div');
    node.className = 'legend-item';
    node.innerHTML = `<strong>${entry.label}</strong><span class="muted">${entry.detail}</span>`;
    legendEl.appendChild(node);
  });
};

const renderRooms = (rooms = []) => {
  roomsEl.innerHTML = '';
  if (!rooms.length) {
    roomsEl.textContent = 'No rooms yet. Create one above to get started!';
    return;
  }

  const template = document.querySelector('#room-template');

  rooms.forEach((room) => {
    const node = template.content.cloneNode(true);
    node.querySelector('.room-owner').textContent = `${room.ownerName}'s lobby`;
    node.querySelector('.room-meta').textContent = `${formatDifficulty(room.difficulty)} · ${room.playerCount}/${room.maxPlayers} players`;

    const details = [];
    details.push(room.status === 'waiting' ? 'Waiting to start' : 'In progress');
    if (room.passwordProtected) {
      details.push('Password required');
    }
    if (!room.allowJoinMidgame) {
      details.push('Locks after start');
    }

    node.querySelector('.room-body').textContent = `${details.join(' • ')} (created ${new Date(
      room.createdAt,
    ).toLocaleTimeString()})`;

    const btn = node.querySelector('.join-room');
    btn.addEventListener('click', async () => {
      await navigator.clipboard.writeText(room.sessionId);
      alert(`Session ID copied: ${room.sessionId}`);
      document.querySelector('#join-session-id').value = room.sessionId;
      document.querySelector('#session-id').value = room.sessionId;
    });

    roomsEl.appendChild(node);
  });
};

const renderLobbyFeed = (messages = [], rooms = []) => {
  lobbyFeedEl.innerHTML = '';
  const feedItems = [
    ...messages.map((message) => ({ type: 'chat', timestamp: message.timestamp, payload: message })),
    ...rooms.map((room) => ({ type: 'room', timestamp: room.createdAt, payload: room })),
  ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  if (!feedItems.length) {
    lobbyFeedEl.textContent = 'Lobby activity will appear here once people start chatting or hosting.';
    return;
  }

  feedItems.forEach((entry) => {
    const container = document.createElement('div');
    container.className = `feed-item ${entry.type}`;

    const meta = document.createElement('div');
    meta.className = 'feed-meta';
    const time = new Date(entry.timestamp).toLocaleTimeString();

    if (entry.type === 'chat') {
      const message = entry.payload;
      const author = document.createElement('span');
      author.className = 'feed-tag';
      author.textContent = message.author;
      meta.append(author, document.createTextNode(time));

      if (message.sessionSummary) {
        const badge = document.createElement('span');
        badge.className = 'feed-pill';
        badge.textContent = `${message.sessionSummary.ownerName}'s lobby`;
        meta.appendChild(badge);
      }

      const body = document.createElement('div');
      body.className = 'feed-body';
      body.textContent = message.body;
      container.append(meta, body);
    }

    if (entry.type === 'room') {
      const room = entry.payload;
      const label = document.createElement('span');
      label.className = 'feed-tag';
      label.textContent = `${room.ownerName} started a lobby`;
      const badge = document.createElement('span');
      badge.className = 'feed-pill';
      badge.textContent = `${formatDifficulty(room.difficulty)} • ${room.playerCount}/${room.maxPlayers}`;
      meta.append(label, document.createTextNode(time), badge);

      const body = document.createElement('div');
      body.className = 'feed-body';
      body.textContent = room.allowJoinMidgame ? 'Mid-dungeon joins allowed' : 'Locks after the run begins';

      const actions = document.createElement('div');
      actions.className = 'feed-actions';
      const copyButton = document.createElement('button');
      copyButton.className = 'pill-button ghost';
      copyButton.textContent = 'Copy Session ID';
      copyButton.addEventListener('click', async () => {
        await navigator.clipboard.writeText(room.sessionId);
        document.querySelector('#join-session-id').value = room.sessionId;
        document.querySelector('#session-id').value = room.sessionId;
        alert(`Session ID copied: ${room.sessionId}`);
      });

      const joinButton = document.createElement('button');
      joinButton.className = 'pill-button';
      joinButton.textContent = 'Join lobby';
      joinButton.addEventListener('click', () => {
        document.querySelector('#join-session-id').value = room.sessionId;
        document.querySelector('#session-id').value = room.sessionId;
        document.querySelector('#chat-session').value = room.sessionId;
        window.scrollTo({ top: document.querySelector('#join-form').offsetTop - 20, behavior: 'smooth' });
      });

      actions.append(copyButton, joinButton);
      container.append(meta, body, actions);
    }

    lobbyFeedEl.appendChild(container);
  });
};

const renderSession = (state) => {
  if (!state) {
    sessionViewEl.textContent = 'Load a session to inspect its state.';
    return;
  }

  const wrapper = document.createElement('div');
  wrapper.className = 'session-summary';

  const heading = document.createElement('h3');
  heading.textContent = `${state.ownerName}'s ${formatDifficulty(state.difficulty)} run (${state.status})`;
  wrapper.appendChild(heading);

  const meta = document.createElement('div');
  meta.className = 'muted';
  meta.textContent = `${state.players.length}/${state.maxPlayers} players · started ${new Date(
    state.createdAt,
  ).toLocaleString()}`;
  wrapper.appendChild(meta);

  const ownerMeta = document.createElement('div');
  ownerMeta.className = 'muted';
  ownerMeta.textContent = `Owner player ID: ${state.ownerId}`;
  wrapper.appendChild(ownerMeta);

  const players = document.createElement('div');
  const list = document.createElement('ul');
  state.players.forEach((player) => {
    const li = document.createElement('li');
    const isActive = state.turn?.currentPlayerId === player.id;
    const prefix = isActive ? '➡️ ' : '';
    li.textContent = `${prefix}${player.name} (${player.id.slice(0, 8)}) on floor ${player.floor + 1} at (${player.position.x}, ${
      player.position.y
    })`;
    list.appendChild(li);
  });
  players.append('Players: ', list);
  wrapper.appendChild(players);

  const dungeonMeta = document.createElement('div');
  const floor = state.dungeon.floors[state.dungeon.currentFloor];
  dungeonMeta.textContent = `Floor ${state.dungeon.currentFloor + 1}/${state.dungeon.floors.length} · ${
    floor.width
  }×${floor.height}${floor.isBasement ? ' (basement)' : ''}`;
  wrapper.appendChild(dungeonMeta);

  const difficultyMeta = document.createElement('div');
  difficultyMeta.className = 'muted';
  difficultyMeta.textContent = `Grid ${state.difficultySettings.width}×${state.difficultySettings.height} · ${state.difficultySettings.minFloors}-${state.difficultySettings.maxFloors} floors`;
  wrapper.appendChild(difficultyMeta);

  const logHeading = document.createElement('h4');
  logHeading.textContent = 'Recent events';
  wrapper.appendChild(logHeading);

  const logList = document.createElement('ul');
  state.log
    .slice()
    .reverse()
    .forEach((entry) => {
      const li = document.createElement('li');
      li.textContent = entry;
      logList.appendChild(li);
    });
  wrapper.appendChild(logList);

  const coords = document.createElement('div');
  coords.textContent = `Grid size: ${state.gridSize} × ${state.gridSize}`;
  wrapper.appendChild(coords);

  sessionViewEl.innerHTML = '';
  sessionViewEl.appendChild(wrapper);
};

const renderStats = (rooms = []) => {
  const totalRooms = rooms.length;
  const filledSeats = rooms.reduce((sum, room) => sum + (room.playerCount || 0), 0);
  const maxSeats = rooms.reduce((sum, room) => sum + (room.maxPlayers || 0), 0);
  const waitingRooms = rooms.filter((room) => room.status === 'waiting').length;

  if (statRoomsEl) {
    statRoomsEl.querySelector('strong').textContent = totalRooms;
    statRoomsEl.querySelector('span').textContent = 'Active sessions';
  }

  if (statPlayersEl) {
    statPlayersEl.querySelector('strong').textContent = maxSeats ? `${filledSeats}/${maxSeats}` : '—';
    statPlayersEl.querySelector('span').textContent = 'Adventurers seated';
  }

  if (statWaitingEl) {
    statWaitingEl.querySelector('strong').textContent = waitingRooms;
    statWaitingEl.querySelector('span').textContent = 'Waiting rooms';
  }
};

const renderOnlineUsers = (rooms = []) => {
  if (!onlineUsersEl) return;
  onlineUsersEl.innerHTML = '';

  const hosts = rooms.map((room) => room.ownerName).filter(Boolean);
  const uniqueHosts = Array.from(new Set(hosts));

  if (!uniqueHosts.length) {
    onlineUsersEl.textContent = 'Waiting for hosts to appear.';
    return;
  }

  uniqueHosts.forEach((host) => {
    const item = document.createElement('div');
    item.textContent = host;
    onlineUsersEl.appendChild(item);
  });
};

const refreshLobby = async () => {
  try {
    statusEl.textContent = 'Loading lobby...';
    const snapshot = await api('/lobby');
    renderRooms(snapshot.rooms);
    renderLobbyFeed(snapshot.messages, snapshot.rooms);
    renderStats(snapshot.rooms);
    renderOnlineUsers(snapshot.rooms);
    statusEl.textContent = `Lobby loaded at ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    statusEl.textContent = error.message;
  }
};

const populateDifficultySelect = () => {
  const select = document.querySelector('#difficulty');
  if (!select) return;
  select.innerHTML = '';
  difficultyDefinitions.forEach((difficulty) => {
    const option = document.createElement('option');
    option.value = difficulty.key;
    option.textContent = difficulty.name;
    select.appendChild(option);
  });
};

const loadDifficulties = async () => {
  try {
    const { difficulties } = await api('/difficulties');
    difficultyDefinitions = difficulties || [];
    populateDifficultySelect();
    renderDifficultyCards();
    renderLegend();
  } catch (error) {
    statusEl.textContent = error.message;
  }
};

const prefillSessionFields = ({ sessionId, playerId }) => {
  const joinId = document.querySelector('#join-session-id');
  const sessionIdInput = document.querySelector('#session-id');
  const startSessionInput = document.querySelector('#start-session-id');
  const startPlayerInput = document.querySelector('#start-player-id');

  if (sessionId) {
    [joinId, sessionIdInput, startSessionInput].forEach((node) => {
      if (node) node.value = sessionId;
    });
  }

  if (playerId && startPlayerInput) {
    startPlayerInput.value = playerId;
  }
};

const createRoomForm = document.querySelector('#create-room-form');
createRoomForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(createRoomForm);
  const payload = Object.fromEntries(formData.entries());
  payload.allowJoinMidgame = formData.get('allowJoinMidgame') === 'on';
  payload.maxPlayers = payload.maxPlayers ? Number(payload.maxPlayers) : undefined;
  payload.password = payload.password || undefined;

  try {
    const result = await api('/lobby/rooms', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    createRoomResultEl.textContent = `Lobby created! Session ID: ${result.sessionId} • Owner player ID: ${result.ownerPlayerId}`;
    prefillSessionFields({ sessionId: result.sessionId, playerId: result.ownerPlayerId });
    refreshLobby();
  } catch (error) {
    createRoomResultEl.textContent = error.message;
  }
});

const chatForm = document.querySelector('#chat-form');
chatForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(chatForm);
  const payload = {
    author: formData.get('chat-author')?.toString() || '',
    body: formData.get('chat-body')?.toString() || '',
    sessionId: formData.get('chat-session')?.toString() || undefined,
  };

  try {
    await api('/lobby/messages', { method: 'POST', body: JSON.stringify(payload) });
    chatForm.reset();
    refreshLobby();
  } catch (error) {
    statusEl.textContent = error.message;
  }
});

const joinForm = document.querySelector('#join-form');
joinForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(joinForm);
  const sessionId = formData.get('join-session-id');
  const payload = {
    playerName: formData.get('join-name'),
    password: formData.get('join-password') || undefined,
  };

  try {
    const response = await api(`/sessions/${sessionId}/join`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    joinResultEl.textContent = `Joined! Player ID: ${response.playerId}`;
    prefillSessionFields({ sessionId, playerId: response.playerId });
    refreshSession(sessionId);
    refreshLobby();
  } catch (error) {
    joinResultEl.textContent = error.message;
  }
});

const sessionForm = document.querySelector('#load-session-form');
sessionForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const sessionId = new FormData(sessionForm).get('session-id');
  prefillSessionFields({ sessionId });
  refreshSession(sessionId);
});

const startForm = document.querySelector('#start-session-form');
startForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(startForm);
  const sessionId = formData.get('start-session-id');
  const playerId = formData.get('start-player-id');

  if (!sessionId || !playerId) return;

  try {
    const response = await api(`/sessions/${sessionId}/start`, {
      method: 'POST',
      body: JSON.stringify({ playerId }),
    });
    startResultEl.textContent = 'Run started!';
    renderSession(response.state);
    refreshLobby();
  } catch (error) {
    startResultEl.textContent = error.message;
  }
});

const refreshSession = async (sessionId) => {
  if (!sessionId) return;
  try {
    const response = await api(`/sessions/${sessionId}`);
    renderSession(response.state);
  } catch (error) {
    sessionViewEl.textContent = error.message;
  }
};

const refreshButton = document.querySelector('#refresh-lobby');
refreshButton?.addEventListener('click', () => refreshLobby());

document.querySelectorAll('[data-scroll]').forEach((button) => {
  button.addEventListener('click', (event) => {
    const target = document.querySelector(event.currentTarget.dataset.scroll);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

const bootstrapLobby = async () => {
  await ensureAuthenticated();
  renderLegend();
  renderSession(null);
  await loadDifficulties();
  await refreshLobby();
};

bootstrapLobby().catch(() => {
  statusEl.textContent = 'Redirecting to sign-in…';
});
