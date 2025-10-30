-- AdventureBot schema and seed data
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `high_scores`;
DROP TABLE IF EXISTS `hub_buttons`;
DROP TABLE IF EXISTS `hub_embeds`;
DROP TABLE IF EXISTS `item_effects`;
DROP TABLE IF EXISTS `enemy_resistances`;
DROP TABLE IF EXISTS `ability_status_effects`;
DROP TABLE IF EXISTS `enemy_abilities`;
DROP TABLE IF EXISTS `intro_steps`;
DROP TABLE IF EXISTS `game_saves`;
DROP TABLE IF EXISTS `game_events`;
DROP TABLE IF EXISTS `enemy_drops`;
DROP TABLE IF EXISTS `enemies`;
DROP TABLE IF EXISTS `chest_instance_rewards`;
DROP TABLE IF EXISTS `treasure_chest_instances`;
DROP TABLE IF EXISTS `chest_def_rewards`;
DROP TABLE IF EXISTS `treasure_chests`;
DROP TABLE IF EXISTS `key_items`;
DROP TABLE IF EXISTS `rooms`;
DROP TABLE IF EXISTS `session_vendor_items`;
DROP TABLE IF EXISTS `session_vendor_instances`;
DROP TABLE IF EXISTS `npc_vendor_items`;
DROP TABLE IF EXISTS `items`;
DROP TABLE IF EXISTS `npc_vendors`;
DROP TABLE IF EXISTS `crystal_templates`;
DROP TABLE IF EXISTS `room_templates`;
DROP TABLE IF EXISTS `floors`;
DROP TABLE IF EXISTS `players`;
DROP TABLE IF EXISTS `session_players`;
DROP TABLE IF EXISTS `sessions`;
DROP TABLE IF EXISTS `class_abilities`;
DROP TABLE IF EXISTS `levels`;
DROP TABLE IF EXISTS `classes`;
DROP TABLE IF EXISTS `abilities`;
DROP TABLE IF EXISTS `status_effects`;
DROP TABLE IF EXISTS `elements`;
DROP TABLE IF EXISTS `floor_room_rules`;
DROP TABLE IF EXISTS `difficulties`;

CREATE TABLE IF NOT EXISTS difficulties (
            difficulty_id       INT AUTO_INCREMENT PRIMARY KEY,
            name                VARCHAR(50) NOT NULL UNIQUE,
            width               INT NOT NULL,
            height              INT NOT NULL,
            min_floors          INT NOT NULL,
            max_floors          INT NOT NULL,
            min_rooms           INT NOT NULL,
            enemy_chance        FLOAT NOT NULL,
            npc_count           INT NOT NULL,
            basement_chance     FLOAT NOT NULL DEFAULT 0.0,
            basement_min_rooms  INT NOT NULL DEFAULT 0,
            basement_max_rooms  INT NOT NULL DEFAULT 0,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS floor_room_rules (
            rule_id           INT AUTO_INCREMENT PRIMARY KEY,
            difficulty_name   VARCHAR(50) NOT NULL,
            floor_number      INT,
            room_type ENUM(
                'safe','monster','item','shop','boss','trap','illusion',
                'staircase_up','staircase_down','exit','locked'
            ) NOT NULL,
            chance            FLOAT   NOT NULL,
            max_per_floor     INT     NOT NULL,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (difficulty_name)
              REFERENCES difficulties(name) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS elements (
            element_id   INT AUTO_INCREMENT PRIMARY KEY,
            element_name VARCHAR(50) NOT NULL UNIQUE,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS status_effects (
            effect_id   INT AUTO_INCREMENT PRIMARY KEY,
            effect_name VARCHAR(100) NOT NULL,
            effect_type ENUM('buff','debuff','neutral') NOT NULL,
            icon_url    VARCHAR(255),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            value       INT NOT NULL,
            duration    INT NOT NULL
        );

CREATE TABLE IF NOT EXISTS abilities (
            ability_id     INT AUTO_INCREMENT PRIMARY KEY,
            ability_name   VARCHAR(100) NOT NULL,
            description    TEXT,
            effect         JSON,
            cooldown       INT DEFAULT 0,
            icon_url       VARCHAR(255),
            target_type    ENUM('self','enemy','ally','any') DEFAULT 'any',
            special_effect VARCHAR(50),
            element_id     INT,
            status_effect_id INT,
            status_duration INT,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scaling_stat   ENUM('attack_power','magic_power','defense') NOT NULL,
            FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE SET NULL,
            FOREIGN KEY (status_effect_id) REFERENCES status_effects(effect_id) ON DELETE SET NULL
        );

CREATE TABLE IF NOT EXISTS classes (
            class_id            INT AUTO_INCREMENT PRIMARY KEY,
            class_name          VARCHAR(50) NOT NULL,
            description         TEXT,
            base_hp             INT DEFAULT 100,
            base_attack         INT DEFAULT 10,
            base_magic          INT DEFAULT 10,
            base_defense        INT DEFAULT 5,
            base_magic_defense  INT DEFAULT 5,
            base_accuracy       INT DEFAULT 95,
            base_evasion        INT DEFAULT 5,
            base_speed          INT DEFAULT 10,
            atb_max             INT DEFAULT 5,
            image_url           VARCHAR(255),
            creator_id          BIGINT,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS levels (
            level                      INT PRIMARY KEY,
            required_exp               INT  NOT NULL,
            hp_increase                FLOAT NOT NULL,
            attack_increase            FLOAT NOT NULL,
            magic_increase             FLOAT NOT NULL,
            defense_increase           FLOAT NOT NULL,
            magic_defense_increase     FLOAT NOT NULL,
            accuracy_increase          FLOAT NOT NULL,
            evasion_increase           FLOAT NOT NULL,
            speed_increase             FLOAT NOT NULL,
            unlocked_abilities         JSON,
            created_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS class_abilities (
            class_id   INT NOT NULL,
            ability_id INT NOT NULL,
            PRIMARY KEY (class_id, ability_id),
            FOREIGN KEY (class_id)   REFERENCES classes(class_id)   ON DELETE CASCADE,
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS sessions (
            session_id    INT AUTO_INCREMENT PRIMARY KEY,
            guild_id      BIGINT NOT NULL,
            thread_id     VARCHAR(64) NOT NULL,
            owner_id      BIGINT NOT NULL,
            num_players   INT NOT NULL,
            current_turn  BIGINT,
            player_turn   BIGINT,
            status        ENUM('active','paused','ended') DEFAULT 'active',
            current_floor INT  DEFAULT 1,
            total_floors  INT  DEFAULT 1,
            difficulty    VARCHAR(50),
            message_id    BIGINT,
            game_log      JSON,
            game_state    JSON,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS session_players (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            session_id  INT NOT NULL,
            player_id   BIGINT NOT NULL,
            joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS players (
            player_id        BIGINT       NOT NULL,
            session_id       INT          NOT NULL,
            username         VARCHAR(100) NOT NULL,
            class_id         INT,
            level            INT DEFAULT 1,
            experience       INT DEFAULT 0,
            hp               INT DEFAULT 100,
            max_hp           INT DEFAULT 100,
            attack_power     INT DEFAULT 10,
            defense          INT DEFAULT 5,
            magic_power      INT DEFAULT 10,
            magic_defense    INT DEFAULT 5,
            accuracy         INT DEFAULT 95,
            evasion          INT DEFAULT 5,
            speed            INT DEFAULT 10,
            coord_x          INT DEFAULT 0,
            coord_y          INT DEFAULT 0,
            current_floor    INT DEFAULT 1,
            inventory        JSON,
            discovered_rooms JSON,
            gil              INT DEFAULT 0,
            enemies_defeated INT DEFAULT 0,
            rooms_visited    INT DEFAULT 0,
            gil_earned       INT DEFAULT 0,
            status_effects   JSON,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, session_id),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (class_id)   REFERENCES classes(class_id)   ON DELETE SET NULL
        );

CREATE TABLE IF NOT EXISTS floors (
            floor_id     INT AUTO_INCREMENT PRIMARY KEY,
            session_id   INT NOT NULL,
            difficulty   VARCHAR(50),
            total_rooms  INT NOT NULL,
            floor_number INT NOT NULL,
            is_goal_floor BOOLEAN DEFAULT FALSE,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS room_templates (
            template_id   INT AUTO_INCREMENT PRIMARY KEY,
            room_type ENUM(
                'safe','monster','item','shop','boss','trap','illusion',
                'staircase_up','staircase_down','exit','locked','chest_unlocked'
            ) NOT NULL,
            template_name VARCHAR(100) NOT NULL,
            description   TEXT,
            image_url     VARCHAR(255),
            default_enemy_id INT,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS crystal_templates (
            template_id   INT AUTO_INCREMENT PRIMARY KEY,
            element_id    INT NOT NULL,
            name          VARCHAR(100) NOT NULL,
            description   TEXT,
            image_url     VARCHAR(255),
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS npc_vendors (
            vendor_id   INT AUTO_INCREMENT PRIMARY KEY,
            vendor_name VARCHAR(100) NOT NULL,
            description TEXT,
            inventory   JSON,
            image_url   VARCHAR(255),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS items (
            item_id      INT AUTO_INCREMENT PRIMARY KEY,
            item_name    VARCHAR(100) NOT NULL,
            description  TEXT,
            effect       JSON,
            type ENUM('consumable','equipment','quest') NOT NULL,
            usage_limit  INT DEFAULT 1,
            price        INT DEFAULT 0,
            store_stock  INT,
            target_type  ENUM('self','enemy','ally','any') DEFAULT 'any',
            image_url    VARCHAR(255),
            creator_id   BIGINT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS npc_vendor_items (
            vendor_id INT NOT NULL,
            item_id   INT NOT NULL,
            price           INT DEFAULT 0,
            stock           INT,
            instance_stock  INT,
            PRIMARY KEY (vendor_id, item_id),
            FOREIGN KEY (vendor_id) REFERENCES npc_vendors(vendor_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id)   REFERENCES items(item_id)        ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS session_vendor_instances (
            session_vendor_id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            vendor_id  INT NOT NULL,
            vendor_name VARCHAR(100) NOT NULL,
            description TEXT,
            image_url   VARCHAR(255),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS session_vendor_items (
            session_vendor_id INT NOT NULL,
            item_id           INT NOT NULL,
            price             INT DEFAULT 0,
            stock             INT,
            instance_stock    INT,
            session_id        INT NOT NULL,
            PRIMARY KEY (session_vendor_id, item_id),
            FOREIGN KEY (session_vendor_id) REFERENCES session_vendor_instances(session_vendor_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id)           REFERENCES items(item_id)              ON DELETE CASCADE,
            FOREIGN KEY (session_id)        REFERENCES sessions(session_id)        ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS rooms (
            room_id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            floor_id   INT NOT NULL,
            coord_x    INT NOT NULL,
            coord_y    INT NOT NULL,
            description TEXT,
            room_type ENUM(
                'safe','monster','item','shop','boss','trap','illusion',
                'staircase_up','staircase_down','exit','locked','chest_unlocked'
            ) NOT NULL,
            image_url VARCHAR(255),
            default_enemy_id INT,
            exits JSON,
            has_encounter BOOLEAN DEFAULT FALSE,
            vendor_id INT,
            stair_up_floor   INT,
            stair_up_x       INT,
            stair_up_y       INT,
            stair_down_floor INT,
            stair_down_x     INT,
            stair_down_y     INT,
            inner_template_id INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (floor_id)   REFERENCES floors(floor_id)     ON DELETE CASCADE,
            FOREIGN KEY (vendor_id)  REFERENCES session_vendor_instances(session_vendor_id) ON DELETE SET NULL,
            FOREIGN KEY (inner_template_id) REFERENCES room_templates(template_id) ON DELETE SET NULL
        );

CREATE TABLE IF NOT EXISTS key_items (
            key_item_id     INT AUTO_INCREMENT PRIMARY KEY,
            name            VARCHAR(100) NOT NULL,
            description     TEXT,
            image_url       VARCHAR(255),
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS treasure_chests (
            chest_id       INT AUTO_INCREMENT PRIMARY KEY,
            chest_name     VARCHAR(100) NOT NULL,
            spawn_weight   FLOAT NOT NULL,
            template_id    INT NOT NULL,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id)
                REFERENCES room_templates(template_id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS chest_def_rewards (
            def_id              INT AUTO_INCREMENT PRIMARY KEY,
            chest_id            INT NOT NULL,
            reward_type         ENUM('gil','item','key') NOT NULL,
            reward_item_id      INT DEFAULT NULL,
            reward_key_item_id  INT DEFAULT NULL,
            amount              INT NOT NULL,
            FOREIGN KEY (chest_id)
                REFERENCES treasure_chests(chest_id)      ON DELETE CASCADE,
            FOREIGN KEY (reward_item_id)
                REFERENCES items(item_id)                 ON DELETE SET NULL,
            FOREIGN KEY (reward_key_item_id)
                REFERENCES key_items(key_item_id)         ON DELETE SET NULL
        );

CREATE TABLE IF NOT EXISTS treasure_chest_instances (
            instance_id       INT AUTO_INCREMENT PRIMARY KEY,
            session_id        INT                                 NOT NULL,
            room_id           INT                                 NOT NULL,
            chest_id          INT                                 NOT NULL,
            floor_id          INT                                 NOT NULL,
            coord_x           INT                                 NOT NULL,
            coord_y           INT                                 NOT NULL,
            step              INT               NOT NULL DEFAULT 1,
            correct_count     INT               NOT NULL DEFAULT 0,
            wrong_count       INT               NOT NULL DEFAULT 0,
            target_number     INT               NOT NULL,
            hint_value        INT               NOT NULL,
            is_unlocked       BOOLEAN           NOT NULL DEFAULT FALSE,
            created_at        TIMESTAMP         DEFAULT CURRENT_TIMESTAMP,
            updated_at        TIMESTAMP         DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id)
                REFERENCES sessions(session_id)         ON DELETE CASCADE,
            FOREIGN KEY (room_id)
                REFERENCES rooms(room_id)               ON DELETE CASCADE,
            FOREIGN KEY (chest_id)
                REFERENCES treasure_chests(chest_id)    ON DELETE CASCADE,
            FOREIGN KEY (floor_id)
                REFERENCES floors(floor_id)             ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS chest_instance_rewards (
            instance_id         INT        NOT NULL,
            reward_type         ENUM('gil','item','key') NOT NULL,
            reward_item_id      INT        NULL,
            reward_key_item_id  INT        NULL,
            reward_amount       INT        NOT NULL DEFAULT 1,
            PRIMARY KEY (
                instance_id,
                reward_type
            ),
            FOREIGN KEY (instance_id)
                REFERENCES treasure_chest_instances(instance_id) ON DELETE CASCADE,
            FOREIGN KEY (reward_item_id)
                REFERENCES items(item_id) ON DELETE SET NULL,
            FOREIGN KEY (reward_key_item_id)
                REFERENCES key_items(key_item_id) ON DELETE SET NULL
        );

CREATE TABLE IF NOT EXISTS enemies (
            enemy_id INT AUTO_INCREMENT PRIMARY KEY,
            enemy_name VARCHAR(50) NOT NULL,
            description TEXT,
            hp INT NOT NULL,
            max_hp INT NOT NULL,
            attack_power INT DEFAULT 10,
            defense INT DEFAULT 5,
            magic_power INT DEFAULT 10,
            magic_defense INT DEFAULT 5,
            accuracy INT DEFAULT 95,
            evasion INT DEFAULT 5,
            atb_max INT DEFAULT 5,
            difficulty VARCHAR(50),
            role VARCHAR(20) DEFAULT 'normal',
            abilities JSON,
            image_url VARCHAR(255),
            spawn_chance FLOAT DEFAULT 0.5,
            gil_drop INT,
            xp_reward INT,
            loot_item_id INT,
            loot_quantity INT DEFAULT 1,
            creator_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loot_item_id) REFERENCES items(item_id) ON DELETE SET NULL
        );

CREATE TABLE IF NOT EXISTS enemy_drops (
            enemy_id INT NOT NULL,
            item_id  INT NOT NULL,
            drop_chance FLOAT NOT NULL,
            min_qty INT DEFAULT 1,
            max_qty INT DEFAULT 1,
            PRIMARY KEY (enemy_id, item_id),
            FOREIGN KEY (enemy_id) REFERENCES enemies(enemy_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id)  REFERENCES items(item_id)  ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS game_events (
            event_id INT AUTO_INCREMENT PRIMARY KEY,
            event_name VARCHAR(100) NOT NULL,
            event_type ENUM('story','battle','item','trap','special') NOT NULL,
            effect JSON,
            floor_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (floor_id) REFERENCES floors(floor_id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS game_saves (
            save_id INT AUTO_INCREMENT PRIMARY KEY,
            guild_id BIGINT NOT NULL,
            save_title VARCHAR(100) NOT NULL,
            save_data JSON NOT NULL,
            timestamp INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS intro_steps (
            intro_step_id INT AUTO_INCREMENT PRIMARY KEY,
            step_order INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            image_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS enemy_abilities (
            enemy_id  INT NOT NULL,
            ability_id INT NOT NULL,
            PRIMARY KEY (enemy_id, ability_id),
            FOREIGN KEY (enemy_id) REFERENCES enemies(enemy_id)   ON DELETE CASCADE,
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS ability_status_effects (
            ability_id INT NOT NULL,
            effect_id  INT NOT NULL,
            PRIMARY KEY (ability_id, effect_id),
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id) ON DELETE CASCADE,
            FOREIGN KEY (effect_id)  REFERENCES status_effects(effect_id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS enemy_resistances (
            enemy_id   INT NOT NULL,
            element_id INT NOT NULL,
            relation   ENUM('weak','resist','absorb','immune','normal') NOT NULL DEFAULT 'normal',
            multiplier FLOAT NOT NULL DEFAULT 1.0,
            PRIMARY KEY (enemy_id, element_id),
            FOREIGN KEY (enemy_id)  REFERENCES enemies(enemy_id)   ON DELETE CASCADE,
            FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS item_effects (
            item_id  INT NOT NULL,
            effect_id INT NOT NULL,
            PRIMARY KEY (item_id, effect_id),
            FOREIGN KEY (item_id)  REFERENCES items(item_id)  ON DELETE CASCADE,
            FOREIGN KEY (effect_id)REFERENCES status_effects(effect_id)ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS hub_embeds (
            embed_id   INT AUTO_INCREMENT PRIMARY KEY,
            embed_type ENUM('main','tutorial','news') NOT NULL,
            title       VARCHAR(255),
            description TEXT,
            image_url   VARCHAR(255),
            text_field  TEXT,
            step_order  INT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS hub_buttons (
            button_id      INT AUTO_INCREMENT PRIMARY KEY,
            embed_type     ENUM('main','tutorial','news') NOT NULL,
            button_label   VARCHAR(50),
            button_custom_id VARCHAR(50),
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE IF NOT EXISTS high_scores (
            score_id         INT AUTO_INCREMENT PRIMARY KEY,
            player_name      VARCHAR(100) NOT NULL,
            guild_id         BIGINT NOT NULL,
            player_level     INT DEFAULT 1,
            player_class     VARCHAR(50),
            gil              INT DEFAULT 0,
            enemies_defeated INT DEFAULT 0,
            bosses_defeated INT DEFAULT 0,
            rooms_visited    INT DEFAULT 0,
            score_value      INT DEFAULT 0,
            difficulty       VARCHAR(50),
            completed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

INSERT INTO `difficulties` (`name`, `width`, `height`, `min_floors`, `max_floors`, `min_rooms`, `enemy_chance`, `npc_count`, `basement_chance`, `basement_min_rooms`, `basement_max_rooms`, `created_at`) VALUES
    ('Easy', 10, 10, 1, 1, 50, 0.2, 2, 0.1, 3, 5, '2025-03-30 21:40:47'),
    ('Medium', 10, 10, 1, 2, 75, 0.25, 3, 0.15, 4, 6, '2025-03-30 21:40:47'),
    ('Hard', 12, 12, 2, 3, 100, 0.3, 3, 0.2, 5, 8, '2025-03-30 21:40:47'),
    ('Crazy Catto', 12, 12, 3, 4, 125, 0.4, 3, 0.25, 6, 10, '2025-03-30 21:40:47');

INSERT INTO `floor_room_rules` (`difficulty_name`, `floor_number`, `room_type`, `chance`, `max_per_floor`) VALUES
    ('Easy', 1, 'safe', 0.5, 20),
    ('Easy', 1, 'monster', 0.3, 10),
    ('Easy', 1, 'item', 0.1, 5),
    ('Easy', 1, 'locked', 0.05, 2),
    ('Easy', 1, 'staircase_up', 0.05, 1),
    ('Easy', NULL, 'boss', 0.0, 1),
    ('Medium', NULL, 'boss', 0.0, 1),
    ('Hard', NULL, 'boss', 0.0, 1),
    ('Crazy Catto', NULL, 'boss', 0.0, 1);

INSERT INTO `elements` (`element_name`, `created_at`) VALUES
    ('Fire', '2025-03-30 21:40:47'),
    ('Ice', '2025-03-30 21:40:47'),
    ('Holy', '2025-03-30 21:40:47'),
    ('Non-Elemental', '2025-03-30 21:40:47'),
    ('Air', '2025-03-30 21:40:47'),
    ('Lightning', '2025-03-30 21:40:47'),
    ('Water', '2025-03-30 21:40:47'),
    ('Earth', '2025-03-30 21:40:47');

INSERT INTO `status_effects` (`effect_name`, `effect_type`, `icon_url`, `created_at`, `value`, `duration`) VALUES
    ('Attack Up', 'buff', '⚔️🔼', '2025-03-31 02:40:47', 0, 0),
    ('Defense Down', 'debuff', '🛡️🔽', '2025-03-31 02:40:47', 0, 0),
    ('Poisoned', 'debuff', '☣️', '2025-03-31 02:40:47', 0, 0),
    ('Regen', 'buff', '❤️🔄', '2025-03-31 02:40:47', 0, 0),
    ('Stun', 'debuff', '🌀', '2025-03-31 02:40:47', 0, 0),
    ('Burn', 'debuff', '🔥', '2025-03-31 02:40:47', 0, 0),
    ('Freeze', 'debuff', '❄️', '2025-03-31 02:40:47', 0, 0),
    ('Bio', 'debuff', '☣️', '2025-05-23 00:10:16', 0, 0),
    ('Silence', 'debuff', '💬', '2025-05-24 21:24:50', 0, 0),
    ('Evasion Up', 'buff', NULL, '2025-05-24 21:25:42', 0, 0),
    ('Blind', 'debuff', NULL, '2025-05-24 21:25:42', 0, 0),
    ('Defense Up', 'buff', '🛡️🔼', '2025-05-24 21:28:44', 0, 0),
    ('Mag.Def Up', 'buff', '🔮🛡️🔼', '2025-05-24 21:28:44', 0, 0),
    ('Mag.Def Down', 'debuff', '🔮🛡️🔽', '2025-05-24 21:33:23', 0, 0),
    ('Berserk', 'neutral', NULL, '2025-05-24 21:34:39', 0, 0),
    ('Magic Up', 'buff', '🔮🔼', '2025-05-24 21:36:05', 0, 0),
    ('Haste', 'buff', '⏱️🔼', '2025-05-24 21:36:06', 0, 0),
    ('Slow', 'debuff', '⏳🔽', '2025-05-24 21:36:07', 0, 0);

INSERT INTO `abilities` (`ability_name`, `description`, `effect`, `cooldown`, `icon_url`, `target_type`, `special_effect`, `element_id`, `status_effect_id`, `status_duration`, `created_at`, `scaling_stat`) VALUES
    ('Cure', 'Heals a small amount of HP.', '{"heal": 50}', 1, '❤️', 'self', NULL, NULL, NULL, NULL, '2025-03-31 07:40:47', 'magic_power'),
    ('Fire', 'Deals fire damage to an enemy.', '{"base_damage": 50}', 1, '🔥', 'enemy', NULL, 1, NULL, NULL, '2025-03-31 07:40:47', 'magic_power'),
    ('Blizzard', 'Deals ice damage to an enemy.', '{"base_damage": 50}', 1, '❄️', 'enemy', NULL, 2, NULL, NULL, '2025-03-31 07:40:47', 'magic_power'),
    ('Holy', 'Deals holy damage to one enemy.', '{"base_damage": 100}', 1, '✨', 'enemy', NULL, 3, NULL, NULL, '2025-03-31 07:40:47', 'magic_power'),
    ('Meteor', 'Massive non‑elemental damage to enemies.', '{"base_damage": 120}', 2, '💫', 'enemy', NULL, 4, NULL, NULL, '2025-03-31 07:40:47', 'magic_power'),
    ('Jump', 'Leap high and strike down a foe.', '{"base_damage": 50}', 5, '🏃‍♂️', 'enemy', NULL, NULL, NULL, NULL, '2025-03-31 07:40:47', 'attack_power'),
    ('Kick', 'Deals physical damage to all enemies.', '{"base_damage": 50}', 3, '🥾', 'enemy', NULL, NULL, NULL, NULL, '2025-03-31 07:40:47', 'attack_power'),
    ('Steal', 'Attempt to steal an item from an enemy.', '{"steal_chance": 50}', 0, '🦹', 'enemy', NULL, NULL, NULL, NULL, '2025-03-31 07:40:47', 'attack_power'),
    ('Scan', 'Reveal an enemy’s HP and weaknesses.', '{"scan": true}', 1, '🔍', 'enemy', NULL, NULL, NULL, NULL, '2025-03-31 07:40:47', 'attack_power'),
    ('Berserk', 'Boost attack but reduce defense.', '{"attack_power": 50, "defense_down": 20}', 3, '💪🔼🛡️', 'self', NULL, NULL, 15, 5, '2025-03-31 07:40:47', 'attack_power'),
    ('Revive', 'Revives a fainted ally with a surge of healing.', '{"heal": 50, "revive": true}', 1, '♻️', 'ally', NULL, NULL, NULL, NULL, '2025-03-31 07:40:47', 'magic_power'),
    ('Thunder', 'Deals lightning damage to an enemy.', '{"base_damage": 50}', 1, '⚡', 'enemy', NULL, 5, NULL, NULL, '2025-03-31 07:40:47', 'magic_power'),
    ('Barrier', 'Raises your defense for a short time.', '{"barrier": {"duration": 3}}', 3, '🛡️🔼', 'self', NULL, NULL, 12, 3, '2025-03-31 07:40:47', 'defense'),
    ('Power Break', 'Lower Enemy Attack Power.', '{"attack_power_down": 10}', 1, '💪🔽', 'enemy', NULL, NULL, 1, 3, '2025-04-03 12:43:43', 'attack_power'),
    ('Armor Break', 'Lower Enemy Defense', '{"defense_down": 30}', 1, '🛡️🔽', 'enemy', NULL, NULL, 2, 3, '2025-04-03 12:43:43', 'attack_power'),
    ('Mental Break', 'Lowers Enemy Magic Power and Magic Defense', '{"magic_power_down": 30, "magic_defense_down": 30}', 1, '🔮🛡️🔽', 'enemy', NULL, NULL, 14, 3, '2025-04-03 12:43:43', 'magic_power'),
    ('Fira', 'Deals greater fire damage to one enemy.', '{"base_damage": 70}', 1, '🔥', 'enemy', NULL, 1, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('FIraga', 'Deals devastating fire damage to one enemy.', '{"base_damage": 90}', 1, '🔥', 'enemy', NULL, 1, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Bizzara', 'Deals greater ice damage to one enemy.', '{"base_damage": 70}', 1, '❄️', 'enemy', NULL, 2, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Bizzaga', 'Deals devastating ice damage to one enemy.', '{"base_damage": 90}', 1, '❄️', 'enemy', NULL, 2, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Thundara', 'Deals greater lightning damage to a single enemy.', '{"base_damage": 70}', 1, '⚡', 'enemy', NULL, 5, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Thundaga', 'Deals devastating lightning damage to a single enemy.', '{"base_damage": 90}', 1, '⚡', 'enemy', NULL, 5, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Flare', 'A massive non‑elemental magic attack dealing significant damage.', '{"base_damage": 100}', 2, '💥', 'enemy', NULL, 4, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Ultima', 'A massive non‑elemental magic attack dealing very high damage.', '{"base_damage": 150}', 3, '🌀', 'enemy', NULL, 4, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Comet', 'A massive non‑elemental magic attack dealing very high damage.', '{"base_damage": 125}', 2, '☄️', 'enemy', NULL, 4, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Cura', 'Heals a greater amount of HP.', '{"heal": 100}', 1, '❤️', 'self', NULL, NULL, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Curaga', 'Heals a high amount of HP.', '{"heal": 200}', 1, '❤️', 'self', NULL, NULL, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Regen', 'Heals a small amount of HP over time.', '{"healing_over_time": {"percent": 0.2, "duration": 10}}', 1, '❤️🔄', 'self', NULL, NULL, 4, 10, '2025-04-03 12:43:43', 'magic_power'),
    ('Shell', 'Raises your magic defense.', '{"magic_defense_up": 30}', 1, '🔮🛡️🔼', 'self', NULL, NULL, 13, 5, '2025-04-03 12:43:43', 'magic_power'),
    ('Blink', 'Raises your evasion.', '{"evasion_up": 30}', 2, '🎯🔼', 'self', NULL, NULL, 10, 5, '2025-04-03 12:43:43', 'magic_power'),
    ('Demi', 'Deals damaged based on enemy health.', '{"percent_damage": 0.25}', 1, '🌀', 'enemy', NULL, 4, NULL, NULL, '2025-04-03 12:43:43', 'attack_power'),
    ('Gravity', 'Deals Air based damage while grounding flying enemies.', '{"base_damage": 80}', 1, '🪐', 'enemy', NULL, NULL, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Haste', 'Grants higher speed with chance of increasing turns.', '{"speed_up": 10, "duration": 5, "status_name": "Haste"}', 5, '⏱️🔼', 'self', NULL, NULL, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Slow', 'Lowers enemy speed with chance of reducing turns.', '{"speed_down": 10, "duration": 5, "status_name": "Slow"}', 5, '⏳🔽', 'enemy', NULL, NULL, NULL, NULL, '2025-04-03 12:43:43', 'magic_power'),
    ('Poison', 'Deals a small amount of damage over time.', '{"damage_over_time": {"duration": 3, "damage_per_turn": 10}}', 3, '☠️', 'enemy', NULL, NULL, 3, 5, '2025-04-03 12:43:43', 'attack_power'),
    ('Bio', 'Deals a greater amount of damage over time.', '{"damage_over_time": {"duration": 5, "damage_per_turn": 12}}', 5, '☣️', 'enemy', NULL, NULL, 8, 5, '2025-04-03 12:43:43', 'attack_power'),
    ('Focus', 'Raises your magic power.', '{"magic_power_up": 30, "duration": 3, "status_name": "Magic Up"}', 1, '🔮🔼', 'self', NULL, NULL, 16, 3, '2025-04-03 12:43:43', 'attack_power'),
    ('Fireblade', 'A Spellblade ability that fuses fire to your attacks.', '{"base_damage": 50}', 1, '🔥⚔️', 'enemy', NULL, 1, NULL, NULL, '2025-04-03 12:51:14', 'attack_power'),
    ('Iceblade', 'A Spellblade ability that fuses ice to your attacks.', '{"base_damage": 50}', 1, '❄️⚔️', 'enemy', NULL, 2, NULL, NULL, '2025-04-03 12:51:14', 'attack_power'),
    ('Thunderblade', 'A Spellblade ability that fuses thunder to your attacks.', '{"base_damage": 50}', 1, '⚡⚔️', 'enemy', NULL, 6, NULL, NULL, '2025-04-03 12:51:14', 'attack_power'),
    ('Heavy Swing', 'A heavy attack dealing medium damage.', '{"base_damage": 50}', 2, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-04-15 01:35:52', 'attack_power'),
    ('Climhazzard', 'A deadly physical attack dealing high damage.', '{"base_damage": 110}', 5, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-04-15 01:59:30', 'attack_power'),
    ('Break', 'Reduce enemy HP to 1.', '{"set_enemy_hp_to": 1}', 5, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-04-15 02:47:21', 'attack_power'),
    ('Demiblade', 'A Spellblade ability that reduces enemy hp by a percentage.', '{"percent_damage": 0.25}', 1, '⚔️', 'enemy', NULL, 4, NULL, NULL, '2025-04-27 19:16:00', 'attack_power'),
    ('Gravityblade', 'A Spellblade ability that fuses gravity magic to your attacks.', '{"base_damage": 80}', 1, '⚔️', 'enemy', NULL, 5, NULL, NULL, '2025-04-27 19:16:00', 'attack_power'),
    ('Silence', 'Stops enemies from using magic for a short time.', NULL, 3, NULL, 'enemy', NULL, NULL, 9, 3, '2025-04-27 19:16:00', 'attack_power'),
    ('BioBlade', 'Deals initial base damage and greater amount of damage over time.', '{"damage_over_time": {"duration": 5, "damage_per_turn": 12}, "non_elemental_damage": 20}', 1, '☣️⚔', 'any', NULL, NULL, 8, 3, '2025-05-01 12:17:43', 'attack_power'),
    ('Lucky 7', 'Deals 7, 77, 777, or 7777 damage if the player HP has a 7 in it. Otherwise deal 1 damage.', '{"lucky_7": true}', 1, '7️⃣', 'enemy', NULL, NULL, NULL, NULL, '2025-05-10 14:38:35', 'attack_power'),
    ('Excalibur', 'Summons the legendary sword to deal massive non-elemental damage.', '{"base_damage": 200}', 5, '⚔️', 'enemy', NULL, 4, NULL, NULL, '2025-05-10 15:12:34', 'attack_power'),
    ('Pilfer Gil', 'Steals Gil from an enemy.', '{"pilfer_gil": true}', 2, '💰', 'enemy', NULL, NULL, NULL, NULL, '2025-05-10 15:12:34', 'attack_power'),
    ('Mug', 'Deals damage while stealing Gil from the enemy.', '{"mug": {"damage": 50}}', 1, '⚔️💰', 'enemy', NULL, NULL, NULL, NULL, '2025-05-10 15:12:34', 'attack_power'),
    ('Light Shot', 'Light attack on an enemy', '{"base_damage": 50}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-10 18:26:42', 'attack_power'),
    ('Heavy Shot', 'Heavy attack on an enemy', '{"base_damage": 150}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-10 18:26:42', 'attack_power'),
    ('Cross-Slash', NULL, '{"base_damage": 200}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Meteorain', NULL, '{"base_damage": 300}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Finishing Touch', NULL, '{"base_damage": 400}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Omnislash', NULL, '{"base_damage": 999}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Stagger', NULL, '{"base_damage": 150}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Bull Charge', NULL, '{"base_damage": 200}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Wallop', NULL, '{"base_damage": 300}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Poisontouch', NULL, '{"damage_over_time": {"duration": 5, "damage_per_turn": 45}}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Grand Lethal', NULL, '{"base_damage": 300}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Bandit', NULL, '{"mug": {"damage": 100}}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Master Thief', NULL, '{"base_damage": 200}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Confuse', NULL, '{"base_damage": 200}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Lancet', NULL, '{"base_damage": 200}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('High Jump', NULL, '{"base_damage": 200}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Eye 4 Eye', NULL, '{"base_damage": 300}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Beast Killer', NULL, '{"base_damage": 400}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Avalanche', NULL, '{"base_damage": 300}', 1, '⚔️', 'enemy', NULL, 2, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('Tornado', NULL, '{"base_damage": 300}', 1, '⚔️', 'enemy', NULL, 5, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('Earthquake', NULL, '{"base_damage": 300}', 1, '⚔️', 'enemy', NULL, 8, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('Meteor', NULL, '{"base_damage": 400}', 1, '⚔️', 'enemy', NULL, 4, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('UltimaBlade', NULL, '{"base_damage": 400}', 1, '⚔️', 'enemy', NULL, 4, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('MeteorBlade', NULL, '{"base_damage": 400}', 1, '⚔️', 'enemy', NULL, 4, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('HolyBlade', NULL, '{"base_damage": 400}', 1, '⚔️', 'enemy', NULL, 3, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('GravijaBlade', NULL, '{"base_damage": 400}', 1, '⚔️', 'enemy', NULL, 5, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('Bio II', NULL, '{"damage_over_time": {"duration": 7, "damage_per_turn": 72}}', 1, '⚔️', 'enemy', NULL, NULL, 8, 7, '2025-05-11 03:48:29', 'attack_power'),
    ('Frog', NULL, '{"base_damage": 0}', 1, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Full-Cure', NULL, '{"heal": 9999}', 1, NULL, 'self', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Reflect', NULL, '{"base_damage": 150}', 1, NULL, 'self', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'attack_power'),
    ('Dbl Holy', NULL, '{"base_damage": 400}', 1, '⚔️', 'enemy', NULL, 3, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('Dbl Ultima', NULL, '{"base_damage": 400}', 1, '⚔️', 'enemy', NULL, 4, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('Dbl Focus', NULL, '{"base_damage": 150}', 1, NULL, 'self', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('Dbl Cure', NULL, '{"heal": 500}', 1, NULL, 'self', NULL, NULL, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('Dbl Flare', NULL, '{"base_damage": 200}', 1, '⚔️', 'enemy', NULL, 4, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('Dbl Dia', NULL, '{"base_damage": 200}', 1, '⚔️', 'enemy', NULL, 3, NULL, NULL, '2025-05-11 03:48:29', 'magic_power'),
    ('White Wind', NULL, '{"healing_over_time": {"percent": 0.05, "duration": 10}}', 0, '❤️', 'self', NULL, NULL, 4, 10, '2025-05-14 01:44:27', 'magic_power'),
    ('Mighty Guard', NULL, '{"barrier": {"duration": 3}}', 0, '🛡️🔼', 'self', NULL, NULL, 12, 3, '2025-05-14 01:44:27', 'attack_power'),
    ('Blue Bullet', NULL, '{"base_damage": 100}', 0, '⚔️', 'enemy', NULL, NULL, NULL, NULL, '2025-05-14 01:45:27', 'attack_power'),
    ('Karma', 'Deals Damage based on turn amount', '{"karma": true}', 3, NULL, 'any', NULL, NULL, NULL, NULL, '2025-05-16 16:13:30', 'attack_power'),
    ('50 Needles', 'Deals 50 damage with 100% hit rate and ignores defense.', '{"base_damage": 47}', 0, NULL, 'any', NULL, NULL, NULL, NULL, '2025-05-22 15:21:04', 'attack_power'),
    ('1,000 Needles', 'Deals 1,000 damage with 100% hit rate and ignores defense.', '{"base_damage": 1000}', 0, NULL, 'any', NULL, NULL, NULL, NULL, '2025-05-22 15:21:04', 'attack_power');

INSERT INTO `classes` (`class_name`, `description`, `base_hp`, `base_attack`, `base_magic`, `base_defense`, `base_magic_defense`, `base_accuracy`, `base_evasion`, `base_speed`, `atb_max`, `image_url`, `creator_id`, `created_at`) VALUES
    ('Warrior', 'A sturdy fighter with strong physical attacks.', 600, 40, 10, 5, 1, 99, 1, 10, 5, 'https://cdn.discordapp.com/attachments/1362832151485354065/1364778448379318442/war.gif?ex=680c39fa&is=680ae87a&hm=80c89e0290ea5ad2432f2d9b265df190741f94309c2bca981ad1885af90671c4&', NULL, '2025-03-31 02:40:47'),
    ('Berserker', 'A savage fighter who channels uncontrollable fury.', 600, 45, 10, 5, 1, 99, 1, 10, 5, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296689379938355/Berserker.gif?ex=680ccb20&is=680b79a0&hm=aa06cfa2c7fb2fb30ffe9e4991d2dda0d4f9420587656a0ddc61b192372ad067&', NULL, '2025-04-03 07:05:45'),
    ('Mystic Knight', 'A hybrid fighter that fuses magic to their blade.', 500, 40, 15, 5, 1, 99, 1, 10, 5, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296718815432724/mystic.gif?ex=680ccb27&is=680b79a7&hm=3f8ad9a2b215496adbc6c0dfd328a9e30621c73e292c40f0fd5ebfb0025bd910&', NULL, '2025-04-03 07:05:45'),
    ('Thief', 'A quick fighter who excels at stealing items.', 500, 45, 10, 5, 1, 99, 1, 10, 5, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296784301363303/thief.gif?ex=680ccb37&is=680b79b7&hm=34ee2d981b968e6de51e52e85c51b3c16ed4ac71974df3ada3f305603d95b59a&', NULL, '2025-03-31 02:40:47'),
    ('Green Mage', 'A powerful mage that manipulates time and space magics.', 500, 20, 20, 5, 1, 99, 1, 10, 5, '', NULL, '2025-03-31 02:40:47'),
    ('Dragoon', 'A lancer who can jump high and strike down foes.', 500, 40, 10, 5, 1, 99, 1, 10, 5, '', NULL, '2025-03-31 02:40:47'),
    ('Bard', 'A ranged attacker wielding a bow and musical influence.', 500, 45, 20, 5, 1, 99, 1, 10, 5, '', NULL, '2025-04-03 07:05:45'),
    ('White Mage', 'A healer who uses holy magic to restore and protect.', 500, 15, 20, 5, 1, 99, 1, 10, 5, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296761723158538/whitemage.gif?ex=680ccb31&is=680b79b1&hm=cd94aeb45272086aac0e5c40507390e5738ef9ee419634a7eded75bf67ea91be&', NULL, '2025-04-03 07:05:45'),
    ('Black Mage', 'A mage who uses destructive elemental spells.', 500, 15, 25, 5, 1, 99, 1, 10, 5, 'https://cdn.discordapp.com/attachments/1362832151485354065/1364772285873127434/blm.gif?ex=680c343d&is=680ae2bd&hm=c3ce479bfd4cd9152348f3bf1d114ce29a63c7c04ac42c7d3ad845ab6bf51eda&', NULL, '2025-04-03 07:05:45'),
    ('Geomancer', 'A sorcerer using environmental/elemental attacks.', 500, 15, 20, 5, 1, 99, 1, 10, 5, 'https://cdn.discordapp.com/attachments/1362832151485354065/1372019632139145237/out.gif?ex=6825405b&is=6823eedb&hm=b0c22f7902cc76c50ce038d3c74dc16559a02e5e3d4262b5173592491bce32e6&', NULL, '2025-04-03 07:05:45'),
    ('Gun Mage', 'A mage clad in blue armor who holds a magic-infused pistol.', 600, 30, 15, 5, 1, 99, 1, 10, 5, 'https://cdn.discordapp.com/attachments/1362832151485354065/1372162446311165983/out.gif?ex=6825c55c&is=682473dc&hm=1e03aac8f24a02d80ee1f48c84a204d43207a75b55259d5bb8c461bb7af6f35e&', NULL, '2025-04-03 07:05:45');

INSERT INTO `levels` (`level`, `required_exp`, `hp_increase`, `attack_increase`, `magic_increase`, `defense_increase`, `magic_defense_increase`, `accuracy_increase`, `evasion_increase`, `speed_increase`, `unlocked_abilities`, `created_at`) VALUES
    (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, NULL, '2025-04-08 10:00:00'),
    (2, 500, 0.1, 0.1, 0.05, 0.05, 0.05, 0, 0, 0.01, NULL, '2025-04-08 10:00:00'),
    (3, 1000, 0.2, 0.15, 0.1, 0.05, 0.07, 0, 0, 0.01, NULL, '2025-04-08 10:00:00'),
    (4, 2000, 0.2, 0.1, 0.1, 0.01, 0.02, 0, 0, 0.01, NULL, '2025-04-09 10:15:49'),
    (5, 3000, 0.2, 0.1, 0.1, 0.01, 0.02, 0, 0, 0.01, NULL, '2025-04-09 10:15:49'),
    (6, 4500, 0.2, 0.1, 0.1, 0.01, 0.02, 0, 0.01, 0.01, NULL, '2025-04-09 10:15:49');

INSERT INTO `class_abilities` (`class_id`, `ability_id`) VALUES
    (8, 1),
    (9, 2),
    (9, 3),
    (8, 4),
    (9, 5),
    (6, 6),
    (1, 7),
    (2, 7),
    (6, 7),
    (4, 9),
    (6, 9),
    (7, 9),
    (2, 10),
    (8, 11),
    (9, 12),
    (10, 13),
    (1, 14),
    (1, 15),
    (1, 16),
    (5, 17),
    (9, 17),
    (9, 18),
    (9, 19),
    (9, 20),
    (9, 21),
    (9, 22),
    (9, 23),
    (10, 23),
    (9, 24),
    (5, 25),
    (8, 26),
    (8, 27),
    (8, 28),
    (10, 31),
    (5, 32),
    (5, 33),
    (7, 33),
    (5, 34),
    (5, 35),
    (9, 36),
    (9, 37),
    (10, 37),
    (3, 38),
    (3, 39),
    (3, 40);

INSERT INTO `room_templates` (`room_type`, `template_name`, `description`, `image_url`, `default_enemy_id`, `created_at`) VALUES
    ('safe', 'Moss Room', 'You do not notice anything of importance, the area appears to be safe.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypemoss.png', NULL, '2025-03-31 02:40:47'),
    ('safe', 'Mystic Room', 'You do not notice anything of importance, the area appears to be safe.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypemystic.png', NULL, '2025-03-31 02:40:47'),
    ('safe', 'Crystal Tunnel', 'You do not notice anything of importance, the area appears to be safe.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/crystals.png', NULL, '2025-03-31 02:40:47'),
    ('safe', 'Bridge', 'You do not notice anything of importance, the area appears to be safe.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypebridge.png', NULL, '2025-04-09 20:22:14'),
    ('safe', 'Magicite', 'You do not notice anything of importance, the area appears to be safe.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypemagicite.png', NULL, '2025-04-09 20:22:19'),
    ('safe', 'Rainbow Crystal', 'You do not notice anything of importance, the area appears to be safe.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/rainbowcrystal.png', NULL, '2025-04-09 20:22:27'),
    ('safe', 'Aetheryte', 'You do not notice any hostile presence; instead you see a naturally growing Aetheryte cluster.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypeaetheryte.png', NULL, '2025-04-09 20:22:27'),
    ('monster', 'You Sense A Hostile Presence...', 'An enemy appears upon entering the area...', '', NULL, '2025-03-31 02:40:47'),
    ('staircase_up', 'Staircase Up', 'A staircase leading upward to the next level.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/stairs_up.png', NULL, '2025-04-19 13:55:00'),
    ('staircase_down', 'Staircase Down', 'A staircase leading downward to the lower level.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/stairs_down.png', NULL, '2025-04-19 13:55:00'),
    ('exit', 'Dungeon Exit', '(Implemented in next patch)', 'https://the-demiurge.com/DemiDevUnit/images/backintro.png', NULL, '2025-03-30 21:40:47'),
    ('item', 'Treasure Room', 'A treasure chest sits in the corner.', 'https://the-demiurge.com/DemiDevUnit/images/backintro.png', NULL, '2025-03-30 21:40:47'),
    ('boss', 'Boss Lair', 'A grand chamber with ominous decorations.', 'https://the-demiurge.com/DemiDevUnit/images/backintro.png', NULL, '2025-03-30 21:40:47'),
    ('trap', 'Trap Room', 'The floor is riddled with hidden traps.', 'https://the-demiurge.com/DemiDevUnit/images/backintro.png', NULL, '2025-03-30 21:40:47'),
    ('shop', 'Shop Room', 'A traveling moogle is seen hiding...', 'https://the-demiurge.com/DemiDevUnit/images/shop/stiltzkin.gif', NULL, '2025-03-30 21:40:47'),
    ('illusion', 'Illusion Chamber', 'The room shimmers mysteriously...', 'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypeillusion.png', NULL, '2025-03-30 21:40:47'),
    ('locked', 'Locked Door', 'A heavy locked door. You need a key.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/locked.png', NULL, '2025-04-19 13:55:00'),
    ('chest_unlocked', 'Unlocked Chest', 'The chest lies open, its contents revealed.', 'https://your.cdn/path/chest_unlocked.png', NULL, '2025-04-23 18:00:00'),
    ('illusion', 'Illusion Chamber', 'Shifting shadows form the shapes of countless foes.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypeillusion.png', NULL, '2025-04-24 12:00:00'),
    ('illusion', 'Illusion Chamber', 'Several doors materialise from thin air, each beckoning.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypeillusion.png', NULL, '2025-04-24 12:00:00'),
    ('illusion', 'Illusion Chamber', 'Glowing elemental crystals illuminate the chamber.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypeillusion.png', NULL, '2025-04-24 12:00:00'),
    ('illusion', 'Empty Illusion Chamber', 'The illusions fade away leaving only an empty space.', 'https://the-demiurge.com/DemiDevUnit/images/rooms/illusion_empty.png', NULL, '2025-04-24 12:00:00');

INSERT INTO `npc_vendors` (`vendor_name`, `description`, `inventory`, `image_url`, `created_at`) VALUES
    ('Stiltzkin', 'Stiltzkin: "Oh hello, I’m glad to see you are not a monster, kupo! I seem to have fallen asleep after getting lost for quite some time, kupo. I’m a traveling merchant, see.. I was portal hopping and suddenly came across a black portal I’d never seen before..."
Stiltzkin looks at you as if he’s trying to recall something. "Have we met before, kupo? You seem familiar."
"At any rate, if you’d like to buy or sell something the shop is still open."', NULL, 'https://the-demiurge.com/DemiDevUnit/images/shop/stiltzkin.gif', '2025-03-24 12:37:28');

INSERT INTO `items` (`item_name`, `description`, `effect`, `type`, `usage_limit`, `price`, `store_stock`, `target_type`, `image_url`, `creator_id`, `created_at`) VALUES
    ('Potion', 'Heals 50 HP.', '{"heal": 50}', 'consumable', 1, 100, 10, 'self', 'https://example.com/icons/potion.png', NULL, '2025-03-30 21:40:47'),
    ('Ether', 'Restores 30 MP.', '{"restore_mp": 30}', 'consumable', 1, 150, 5, 'self', 'https://example.com/icons/ether.png', NULL, '2025-03-30 21:40:47'),
    ('Phoenix Down', 'Revives a fainted ally with 100 HP.', '{"heal": 100, "revive": true}', 'consumable', 1, 500, 2, 'ally', 'https://example.com/icons/phoenix_down.png', NULL, '2025-03-30 21:40:47');

INSERT INTO `npc_vendor_items` (`vendor_id`, `item_id`, `price`, `stock`, `instance_stock`) VALUES
    (1, 1, 50, 1, 2),
    (1, 3, 100, 1, 1);

INSERT INTO `enemies` (`enemy_name`, `description`, `hp`, `max_hp`, `attack_power`, `defense`, `magic_power`, `magic_defense`, `accuracy`, `evasion`, `atb_max`, `difficulty`, `role`, `abilities`, `image_url`, `spawn_chance`, `gil_drop`, `xp_reward`, `loot_item_id`, `loot_quantity`, `creator_id`, `created_at`) VALUES
    ('Behemoth', 'large, purple, canine-esque creature...', 100, 100, 15, 5, 5, 5, 90, 5, 5, 'Easy', 'normal', NULL, 'http://the-demiurge.com/DemiDevUnit/images/monsters/behemoth.png', 0.3, 100, 75, NULL, 1, NULL, '2025-03-31 02:40:47'),
    ('Ghost', 'pale, translucent, or wispy being...', 50, 50, 10, 5, 5, 3, 85, 5, 5, 'Easy', 'normal', NULL, 'http://the-demiurge.com/DemiDevUnit/images/monsters/ghost.png', 0.3, 50, 50, NULL, 2, NULL, '2025-03-31 02:40:47'),
    ('Dragon Whelp', 'A young dragon spitting small flames.', 100, 100, 15, 8, 10, 5, 80, 10, 5, 'Hard', 'normal', NULL, 'https://example.com/images/dragon_whelp.png', 0.1, 150, 150, NULL, 1, NULL, '2025-03-31 02:40:47'),
    ('Lich', 'An undead sorcerer with devastating magic.', 80, 80, 12, 4, 20, 10, 90, 5, 5, 'Hard', 'normal', NULL, 'https://example.com/images/lich.png', 0.2, 200, 200, NULL, 1, NULL, '2025-03-31 02:40:47'),
    ('Dark Knight', 'A mysterious warrior clad in obsidian armor.', 120, 120, 20, 10, 5, 8, 85, 5, 5, 'Medium', 'normal', NULL, 'https://example.com/images/dark_knight.png', 0.4, 150, 250, NULL, 1, NULL, '2025-03-31 02:40:47'),
    ('Nightmare', 'You feel a sudden wave of fear as the dark shrouded creature approaches...', 125, 125, 20, 6, 6, 6, 90, 5, 5, 'Easy', 'normal', NULL, 'http://the-demiurge.com/DemiDevUnit/images/monsters/elementals/nightmare_elemental.png', 0.1, 125, 150, NULL, 1, NULL, '2025-04-09 20:20:32'),
    ('Tonberry Chef', 'A creature said to be only in legend. It seems to like cooking, but where did it get that knife and chef''s hat? Also VERY big.', 250, 250, 20, 6, 10, 6, 90, 5, 5, 'Easy', 'normal', NULL, 'http://the-demiurge.com/DemiDevUnit/images/monsters/tonberry/tonberry_chef.png', 0.1, 150, 110, NULL, 1, NULL, '2025-04-09 20:20:32'),
    ('Overgrown Tonberry', 'A creature said to be only in legend. Also VERY big.', 200, 200, 10, 5, 2, 3, 85, 5, 5, 'Easy', 'normal', NULL, 'http://the-demiurge.com/DemiDevUnit/images/monsters/tonberry/overgrown_tonberry.png', 0.3, 75, 90, NULL, 1, NULL, '2025-03-31 02:40:47');

INSERT INTO `enemy_abilities` (`enemy_id`, `ability_id`) VALUES
    (1, 2),
    (2, 2),
    (3, 2),
    (4, 2),
    (4, 3),
    (1, 7),
    (2, 7),
    (3, 7),
    (6, 7),
    (2, 9),
    (4, 9),
    (5, 10),
    (6, 10),
    (5, 12);

INSERT INTO `enemy_drops` (`enemy_id`, `item_id`, `drop_chance`, `min_qty`, `max_qty`) VALUES
    (1, 1, 0.5, 1, 1),
    (2, 3, 0.25, 1, 1),
    (4, 1, 0.25, 1, 1);

INSERT INTO `enemy_resistances` (`enemy_id`, `element_id`, `relation`, `multiplier`) VALUES
    (1, 1, 'weak', 1.5),
    (2, 3, 'absorb', -1.0),
    (3, 2, 'resist', 0.5);

INSERT INTO `intro_steps` (`step_order`, `title`, `description`, `image_url`, `created_at`) VALUES
    (1, 'An Unexpected Discovery', 'During what began as an ordinary raid, Sophia paused...', 'https://the-demiurge.com/DemiDevUnit/images/intro/step1.png', '2025-03-31 02:40:47'),
    (2, 'Mog''s Bold Venture', 'As the group hesitated, a tiny figure fluttered forward...', 'https://the-demiurge.com/DemiDevUnit/images/intro/step2.png', '2025-03-31 02:40:47'),
    (3, 'The Moogle Returns', 'Moments felt like hours as the group waited anxiously...', 'https://the-demiurge.com/DemiDevUnit/images/intro/step3.png', '2025-03-31 02:40:47'),
    (4, 'Sophia''s Decision', 'Sophia nodded solemnly...', 'https://the-demiurge.com/DemiDevUnit/images/intro/step4.png', '2025-04-09 09:37:27'),
    (5, 'The Call to Adventure', 'Returning to their Free Company house, Sophia gathered everyone...', 'https://the-demiurge.com/DemiDevUnit/images/intro/step5.png', '2025-04-09 09:37:27');

INSERT INTO `ability_status_effects` (`ability_id`, `effect_id`) VALUES
    (10, 1),
    (10, 2),
    (35, 3),
    (36, 8),
    (33, 17),
    (34, 18),
    (46, 9);

INSERT INTO `hub_embeds` (`embed_type`, `title`, `description`, `image_url`, `text_field`, `step_order`, `created_at`) VALUES
    ('main', '', 'Welcome to AdventureBot, a classic turn based dungeon crawler...', 'https://the-demiurge.com/DemiDevUnit/images/embed.png', 'AdventureBot v3.0.2 is now Live!', NULL, '2025-03-31 03:43:19'),
    ('tutorial', 'Starting A Game', '
Click **New Game** to create your own session thread. You''re placed in the queue automatically.

Other players join by pressing **Join Game** on the LFG post in the game channel—only they should use this button.

Up to 6 players can join directly; extra players appear in the **Queue List** inside the thread.

When the creator is ready, they press **Start Game** to lock in the party.

', 'https://cdn.discordapp.com/attachments/1362832151485354065/1373622234865733652/Screenshot_2025-05-18_at_6.14.47_AM.png?ex=682b14e5&is=6829c365&hm=b91a3c24ed88f1f493db9a8f61473923e316e284782ab15bd565f6a82ac25966&', 'Coming Soon...', 1, '2025-04-15 02:50:10'),
    ('tutorial', 'Choose Class and Difficulty', 'Once the Session Creator clicks the Start Game button they can choose their class and difficulty level.

- Selecting **Easy** will generate up to 2 floors with a rare chance to spawn a basement floor. In this mode most harder enemeis are removed from generation.

- Choosing **Medium** difficulty will generate up to 4 floors with at least 2 and a rare chance to spawn a basement. In this mode harder enemies spawn along side easy ones during generation.

- Selecting **Hard** is exactly what you think it is. With up to 4 floors and higher spawn chances on more difficult enemies and less vendor shops and item drops.

- **Crazy Catto** is the most difficult of challenges and well... you''d be a crazy catto to try it.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1373622403455778848/Screenshot_2025-05-18_at_6.19.11_AM.png?ex=682b150d&is=6829c38d&hm=045419693ca1ecd758f7ecf5c7208ca4da321622636b908da9e15c99f97dde61&', 'Coming Soon...', 2, '2025-04-17 03:45:05');

SET FOREIGN_KEY_CHECKS = 1;
