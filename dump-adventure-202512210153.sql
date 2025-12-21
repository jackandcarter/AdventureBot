/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.13-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: adventure
-- ------------------------------------------------------
-- Server version	10.11.13-MariaDB-0ubuntu0.24.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `abilities`
--

DROP TABLE IF EXISTS `abilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `abilities` (
  `ability_id` int(11) NOT NULL AUTO_INCREMENT,
  `ability_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `effect` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`effect`)),
  `cooldown` int(11) DEFAULT 0,
  `mp_cost` int(11) DEFAULT 0,
  `icon_url` varchar(255) DEFAULT NULL,
  `target_type` enum('self','enemy','ally','any') DEFAULT 'any',
  `special_effect` varchar(50) DEFAULT NULL,
  `element_id` int(11) DEFAULT NULL,
  `status_effect_id` int(11) DEFAULT NULL,
  `status_duration` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `scaling_stat` enum('attack_power','magic_power','defense') NOT NULL,
  PRIMARY KEY (`ability_id`),
  KEY `element_id` (`element_id`),
  KEY `status_effect_id` (`status_effect_id`),
  CONSTRAINT `abilities_ibfk_1` FOREIGN KEY (`element_id`) REFERENCES `elements` (`element_id`) ON DELETE SET NULL,
  CONSTRAINT `abilities_ibfk_2` FOREIGN KEY (`status_effect_id`) REFERENCES `status_effects` (`effect_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=207 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `abilities`
--

LOCK TABLES `abilities` WRITE;
/*!40000 ALTER TABLE `abilities` DISABLE KEYS */;
INSERT INTO `abilities` VALUES
(1,'Cure','Heals a small amount of HP.','{\"heal_current_pct\": 0.35}',1,0,'❤️','self',NULL,NULL,NULL,NULL,'2025-03-31 12:40:47','magic_power'),
(2,'Fire','Deals fire damage to an enemy.','{\"base_damage\": 50}',1,0,'🔥','enemy',NULL,1,NULL,NULL,'2025-03-31 12:40:47','magic_power'),
(3,'Blizzard','Deals ice damage to an enemy.','{\"base_damage\": 50}',1,0,'❄️','enemy',NULL,2,NULL,NULL,'2025-03-31 12:40:47','magic_power'),
(4,'Holy','Deals holy damage to one enemy.','{\"base_damage\": 100}',1,0,'✨','enemy',NULL,3,NULL,NULL,'2025-03-31 12:40:47','magic_power'),
(5,'Meteor','Massive non‑elemental damage to enemies.','{\"base_damage\": 120}',2,0,'💫','enemy',NULL,4,NULL,NULL,'2025-03-31 12:40:47','magic_power'),
(6,'Jump','Leap high and strike down a foe.','{\"base_damage\": 50}',5,0,'🏃‍♂️','enemy',NULL,NULL,NULL,NULL,'2025-03-31 12:40:47','attack_power'),
(7,'Kick','Deals physical damage to all enemies.','{\"base_damage\": 50}',3,0,'🥾','enemy',NULL,NULL,NULL,NULL,'2025-03-31 12:40:47','attack_power'),
(8,'Steal','Attempt to steal an item from an enemy.','{\"steal_chance\": 50}',0,0,'🦹','enemy',NULL,NULL,NULL,NULL,'2025-03-31 12:40:47','attack_power'),
(9,'Scan','Reveal an enemy’s HP and weaknesses.','{\"scan\": true}',1,0,'🔍','enemy',NULL,NULL,NULL,NULL,'2025-03-31 12:40:47','attack_power'),
(10,'Berserk','Boost attack but reduce defense.','{\"attack_power\": 50, \"defense_down\": 20}',3,0,'💪🔼🛡️','self',NULL,NULL,15,5,'2025-03-31 12:40:47','attack_power'),
(11,'Revive','Revives a fainted ally with a surge of healing.','{\"heal\": 50, \"revive\": true}',1,0,'♻️','ally',NULL,NULL,NULL,NULL,'2025-03-31 12:40:47','magic_power'),
(12,'Thunder','Deals lightning damage to an enemy.','{\"base_damage\": 50}',1,0,'⚡','enemy',NULL,5,NULL,NULL,'2025-03-31 12:40:47','magic_power'),
(13,'Barrier','Raises your defense for a short time.','{\"barrier\": {\"duration\": 3}}',3,0,'🛡️🔼','self',NULL,NULL,12,3,'2025-03-31 12:40:47','defense'),
(14,'Power Break','Lower Enemy Attack Power.','{\"attack_power_down\": 10}',1,0,'💪🔽','enemy',NULL,NULL,1,3,'2025-04-03 17:43:43','attack_power'),
(15,'Armor Break','Lower Enemy Defense','{\"defense_down\": 30}',1,0,'🛡️🔽','enemy',NULL,NULL,2,3,'2025-04-03 17:43:43','attack_power'),
(16,'Mental Break','Lowers Enemy Magic Power and Magic Defense','{\"magic_power_down\": 30, \"magic_defense_down\": 30}',1,0,'🔮🛡️🔽','enemy',NULL,NULL,14,3,'2025-04-03 17:43:43','magic_power'),
(17,'Fira','Deals greater fire damage to one enemy.','{\"base_damage\": 70}',1,0,'🔥','enemy',NULL,1,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(18,'FIraga','Deals devastating fire damage to one enemy.','{\"base_damage\": 90}',1,0,'🔥','enemy',NULL,1,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(19,'Bizzara','Deals greater ice damage to one enemy.','{\"base_damage\": 70}',1,0,'❄️','enemy',NULL,2,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(20,'Bizzaga','Deals devastating ice damage to one enemy.','{\"base_damage\": 90}',1,0,'❄️','enemy',NULL,2,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(21,'Thundara','Deals greater lightning damage to a single enemy.','{\"base_damage\": 70}',1,0,'⚡','enemy',NULL,5,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(22,'Thundaga','Deals devastating lightning damage to a single enemy.','{\"base_damage\": 90}',1,0,'⚡','enemy',NULL,5,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(23,'Flare','A massive non‑elemental magic attack dealing significant damage.','{\"base_damage\": 100}',2,0,'💥','enemy',NULL,4,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(24,'Ultima','A massive non‑elemental magic attack dealing very high damage.','{\"base_damage\": 150}',3,0,'🌀','enemy',NULL,4,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(25,'Comet','A massive non‑elemental magic attack dealing very high damage.','{\"base_damage\": 125}',2,0,'☄️','enemy',NULL,4,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(26,'Cura','Heals a greater amount of HP.','{\"heal_current_pct\": 0.75}',1,0,'❤️','self',NULL,NULL,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(27,'Curaga','Heals a high amount of HP.','{\"heal_current_pct\": 1.0}',1,0,'❤️','self',NULL,NULL,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(28,'Regen','Heals a small amount of HP over time.','{\"healing_over_time\": {\"percent\": 0.2, \"duration\": 10}}',1,0,'❤️🔄','self',NULL,NULL,4,10,'2025-04-03 17:43:43','magic_power'),
(29,'Shell','Raises your magic defense.','{\"magic_defense_up\": 30}',1,0,'🔮🛡️🔼','self',NULL,NULL,13,5,'2025-04-03 17:43:43','magic_power'),
(30,'Blink','Raises your evasion.','{\"evasion_up\": 30}',2,0,'🎯🔼','self',NULL,NULL,10,5,'2025-04-03 17:43:43','magic_power'),
(31,'Demi','Deals damaged based on enemy health.','{\"percent_damage\": 0.25}',1,0,'🌀','enemy',NULL,4,NULL,NULL,'2025-04-03 17:43:43','attack_power'),
(32,'Gravity','Deals Air based damage while grounding flying enemies.','{\"base_damage\": 80}',1,0,'🪐','enemy',NULL,NULL,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(33,'Haste','Grants higher speed with chance of increasing turns.',NULL,3,0,'⏱️🔼','self',NULL,NULL,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(34,'Slow','Lowers enemy speed with chance of reducing turns.',NULL,2,0,'⏳🔽','enemy',NULL,NULL,NULL,NULL,'2025-04-03 17:43:43','magic_power'),
(35,'Poison','Deals a small amount of damage over time.','{\"damage_over_time\": {\"duration\": 3, \"damage_per_turn\": 10}}',3,0,'☠️','enemy',NULL,NULL,3,5,'2025-04-03 17:43:43','attack_power'),
(36,'Bio','Deals a greater amount of damage over time.','{\"damage_over_time\": {\"duration\": 5, \"damage_per_turn\": 12}}',5,0,'☣️','enemy',NULL,NULL,8,5,'2025-04-03 17:43:43','attack_power'),
(37,'Focus','Raises your magic power.','{\"magic_power_up\": 30}',1,0,'🔮🔼','self',NULL,NULL,16,5,'2025-04-03 17:43:43','attack_power'),
(38,'Fireblade','A Spellblade ability that fuses fire to your attacks.','{\"base_damage\": 50}',1,0,'🔥⚔️','enemy',NULL,1,NULL,NULL,'2025-04-03 17:51:14','attack_power'),
(39,'Iceblade','A Spellblade ability that fuses ice to your attacks.','{\"base_damage\": 50}',1,0,'❄️⚔️','enemy',NULL,2,NULL,NULL,'2025-04-03 17:51:14','attack_power'),
(40,'Thunderblade','A Spellblade ability that fuses thunder to your attacks.','{\"base_damage\": 50}',1,0,'⚡⚔️','enemy',NULL,6,NULL,NULL,'2025-04-03 17:51:14','attack_power'),
(41,'Heavy Swing','A heavy attack dealing medium damage.','{\"base_damage\": 50}',2,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-04-15 06:35:52','attack_power'),
(42,'Climhazzard','A deadly physical attack dealing high damage.','{\"base_damage\": 110}',5,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-04-15 06:59:30','attack_power'),
(43,'Break','Reduce enemy HP to 1.','{\"set_enemy_hp_to\": 1}',5,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-04-15 07:47:21','attack_power'),
(44,'Demiblade','A Spellblade ability that reduces enemy hp by a percentage.','{\"percent_damage\": 0.25}',1,0,'⚔️','enemy',NULL,4,NULL,NULL,'2025-04-28 00:16:00','attack_power'),
(45,'Gravityblade','A Spellblade ability that fuses gravity magic to your attacks.','{\"base_damage\": 80}',1,0,'⚔️','enemy',NULL,5,NULL,NULL,'2025-04-28 00:16:00','attack_power'),
(46,'Silence','Stops enemies from using magic for a short time.',NULL,1,0,NULL,'enemy',NULL,NULL,9,3,'2025-04-28 00:16:00','attack_power'),
(47,'BioBlade','Deals initial base damage and greater amount of damage over time.','{\"damage_over_time\": {\"duration\": 5, \"damage_per_turn\": 12}, \"non_elemental_damage\": 20}',1,0,'☣️⚔','any',NULL,NULL,8,3,'2025-05-01 17:17:43','attack_power'),
(48,'Lucky 7','Deals 7, 77, 777, or 7777 damage if the player HP has a 7 in it. Otherwise deal 1 damage.','{\"lucky_7\": true}',1,0,'7️⃣','enemy',NULL,NULL,NULL,NULL,'2025-05-10 19:38:35','attack_power'),
(49,'Excalibur','Summons the legendary sword to deal massive non-elemental damage.','{\"base_damage\": 200}',5,0,'⚔️','enemy',NULL,4,NULL,NULL,'2025-05-10 20:12:34','attack_power'),
(50,'Pilfer Gil','Steals Gil from an enemy.','{\"pilfer_gil\": true}',2,0,'💰','enemy',NULL,NULL,NULL,NULL,'2025-05-10 20:12:34','attack_power'),
(51,'Mug','Deals damage while stealing Gil from the enemy.','{\"mug\": {\"damage\": 50}}',1,0,'⚔️💰','enemy',NULL,NULL,NULL,NULL,'2025-05-10 20:12:34','attack_power'),
(52,'Light Shot','Light attack on an enemy','{\"base_damage\": 50}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-10 23:26:42','attack_power'),
(53,'Heavy Shot','Heavy attack on an enemy','{\"base_damage\": 150}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-10 23:26:42','attack_power'),
(54,'Cross-Slash',NULL,'{\"base_damage\": 200}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(55,'Meteorain',NULL,'{\"base_damage\": 300}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(56,'Finishing Touch',NULL,'{\"base_damage\": 400}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(57,'Omnislash',NULL,'{\"base_damage\": 999}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(58,'Stagger',NULL,'{\"base_damage\": 150}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(59,'Bull Charge',NULL,'{\"base_damage\": 200}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(60,'Wallop',NULL,'{\"base_damage\": 300}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(61,'Poisontouch',NULL,'{\"damage_over_time\": {\"duration\": 5, \"damage_per_turn\": 45}}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(62,'Grand Lethal',NULL,'{\"base_damage\": 300}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(63,'Bandit',NULL,'{\"mug\": {\"damage\": 100}}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(64,'Master Thief',NULL,'{\"base_damage\": 200}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(65,'Confuse',NULL,'{\"base_damage\": 200}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(66,'Lancet',NULL,'{\"base_damage\": 200}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(67,'High Jump',NULL,'{\"base_damage\": 200}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(68,'Eye 4 Eye',NULL,'{\"base_damage\": 300}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(69,'Beast Killer',NULL,'{\"base_damage\": 400}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(70,'Avalanche',NULL,'{\"base_damage\": 300}',1,0,'⚔️','enemy',NULL,2,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(71,'Tornado',NULL,'{\"base_damage\": 300}',1,0,'⚔️','enemy',NULL,5,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(72,'Earthquake',NULL,'{\"base_damage\": 300}',1,0,'⚔️','enemy',NULL,8,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(73,'Meteor',NULL,'{\"base_damage\": 400}',1,0,'⚔️','enemy',NULL,4,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(74,'UltimaBlade',NULL,'{\"base_damage\": 400}',1,0,'⚔️','enemy',NULL,4,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(75,'MeteorBlade',NULL,'{\"base_damage\": 400}',1,0,'⚔️','enemy',NULL,4,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(76,'HolyBlade',NULL,'{\"base_damage\": 400}',1,0,'⚔️','enemy',NULL,3,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(77,'GravijaBlade',NULL,'{\"base_damage\": 400}',1,0,'⚔️','enemy',NULL,5,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(78,'Bio II',NULL,'{\"damage_over_time\": {\"duration\": 7, \"damage_per_turn\": 72}}',1,0,'⚔️','enemy',NULL,NULL,8,7,'2025-05-11 08:48:29','attack_power'),
(79,'Frog',NULL,'{\"base_damage\": 0}',1,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(80,'Full-Cure',NULL,'{\"heal\": 9999}',1,0,NULL,'self',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(81,'Reflect',NULL,'{\"base_damage\": 150}',1,0,NULL,'self',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','attack_power'),
(82,'Dbl Holy',NULL,'{\"base_damage\": 400}',1,0,'⚔️','enemy',NULL,3,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(83,'Dbl Ultima',NULL,'{\"base_damage\": 400}',1,0,'⚔️','enemy',NULL,4,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(84,'Dbl Focus',NULL,'{\"base_damage\": 150}',1,0,NULL,'self',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(85,'Dbl Cure',NULL,'{\"heal\": 500}',1,0,NULL,'self',NULL,NULL,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(86,'Dbl Flare',NULL,'{\"base_damage\": 200}',1,0,'⚔️','enemy',NULL,4,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(87,'Dbl Dia',NULL,'{\"base_damage\": 200}',1,0,'⚔️','enemy',NULL,3,NULL,NULL,'2025-05-11 08:48:29','magic_power'),
(88,'White Wind',NULL,'{\"healing_over_time\": {\"percent\": 0.05, \"duration\": 10}}',0,0,'❤️','self',NULL,NULL,4,10,'2025-05-14 06:44:27','magic_power'),
(89,'Mighty Guard',NULL,'{\"barrier\": {\"duration\": 3}}',0,0,'🛡️🔼','self',NULL,NULL,12,3,'2025-05-14 06:44:27','attack_power'),
(90,'Blue Bullet',NULL,'{\"base_damage\": 100}',0,0,'⚔️','enemy',NULL,NULL,NULL,NULL,'2025-05-14 06:45:27','attack_power'),
(91,'Karma','Deals Damage based on turn amount','{\"karma\": true}',3,0,NULL,'any',NULL,NULL,NULL,NULL,'2025-05-16 21:13:30','attack_power'),
(92,'50 Needles','Deals 50 damage with 100% hit rate and ignores defense.','{\"flat_damage\": 50}',0,0,NULL,'any',NULL,NULL,NULL,NULL,'2025-05-22 20:21:04','attack_power'),
(93,'1,000 Needles','Deals 1,000 damage with 100% hit rate and ignores defense.','{\"flat_damage\": 1000}',0,0,NULL,'any',NULL,NULL,NULL,NULL,'2025-05-22 20:21:04','attack_power'),
(201,'Hellfire','Engulf the enemy in infernal flames.','{\"base_damage\": 160}',2,35,'🔥','enemy',NULL,1,NULL,NULL,'2025-07-01 05:00:00','magic_power'),
(202,'Diamond Dust','Unleash a frozen tempest.','{\"base_damage\": 160}',2,35,'❄️','enemy',NULL,2,NULL,NULL,'2025-07-01 05:00:00','magic_power'),
(203,'Judgment Bolt','Call down a thunderous strike.','{\"base_damage\": 175}',3,40,'⚡','enemy',NULL,6,NULL,NULL,'2025-07-01 05:00:00','magic_power'),
(204,'Inferno','Engulf the enemy in infernal flames.','{\"base_damage\": 275}',0,0,NULL,'enemy',NULL,1,6,10,'2025-12-20 23:44:43','magic_power'),
(205,'Cold Snap','Freeze Enemies while causing damage.','{\"base_damage\": 275}',0,0,NULL,'enemy',NULL,2,7,10,'2025-12-20 23:44:43','magic_power'),
(206,'Storm Tempest','Stun your foe with a devistating storm.','{\"base_damage\": 275}',0,0,NULL,'enemy',NULL,6,5,10,'2025-12-20 23:44:43','magic_power');
/*!40000 ALTER TABLE `abilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ability_status_effects`
--

DROP TABLE IF EXISTS `ability_status_effects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `ability_status_effects` (
  `ability_id` int(11) NOT NULL,
  `effect_id` int(11) NOT NULL,
  PRIMARY KEY (`ability_id`,`effect_id`),
  KEY `effect_id` (`effect_id`),
  CONSTRAINT `ability_status_effects_ibfk_1` FOREIGN KEY (`ability_id`) REFERENCES `abilities` (`ability_id`) ON DELETE CASCADE,
  CONSTRAINT `ability_status_effects_ibfk_2` FOREIGN KEY (`effect_id`) REFERENCES `status_effects` (`effect_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ability_status_effects`
--

LOCK TABLES `ability_status_effects` WRITE;
/*!40000 ALTER TABLE `ability_status_effects` DISABLE KEYS */;
INSERT INTO `ability_status_effects` VALUES
(10,1),
(10,2),
(33,17),
(34,18),
(35,3),
(36,8),
(46,9);
/*!40000 ALTER TABLE `ability_status_effects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chest_def_rewards`
--

DROP TABLE IF EXISTS `chest_def_rewards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `chest_def_rewards` (
  `def_id` int(11) NOT NULL AUTO_INCREMENT,
  `chest_id` int(11) NOT NULL,
  `reward_type` enum('gil','item','key') NOT NULL,
  `reward_item_id` int(11) DEFAULT NULL,
  `reward_key_item_id` int(11) DEFAULT NULL,
  `amount` int(11) NOT NULL,
  `spawn_weight` float NOT NULL DEFAULT 1,
  PRIMARY KEY (`def_id`),
  KEY `chest_id` (`chest_id`),
  KEY `reward_item_id` (`reward_item_id`),
  KEY `reward_key_item_id` (`reward_key_item_id`),
  CONSTRAINT `chest_def_rewards_ibfk_1` FOREIGN KEY (`chest_id`) REFERENCES `treasure_chests` (`chest_id`) ON DELETE CASCADE,
  CONSTRAINT `chest_def_rewards_ibfk_2` FOREIGN KEY (`reward_item_id`) REFERENCES `items` (`item_id`) ON DELETE SET NULL,
  CONSTRAINT `chest_def_rewards_ibfk_3` FOREIGN KEY (`reward_key_item_id`) REFERENCES `key_items` (`key_item_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chest_def_rewards`
--

LOCK TABLES `chest_def_rewards` WRITE;
/*!40000 ALTER TABLE `chest_def_rewards` DISABLE KEYS */;
INSERT INTO `chest_def_rewards` VALUES
(1,1,'key',7,NULL,1,0.6),
(2,2,'item',5,NULL,1,1),
(3,1,'key',8,NULL,1,0.3),
(4,3,'gil',NULL,NULL,500,0.8),
(5,1,'key',7,NULL,1,0.6),
(6,1,'key',8,NULL,1,0.3),
(7,3,'gil',NULL,NULL,500,0.8);
/*!40000 ALTER TABLE `chest_def_rewards` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chest_instance_rewards`
--

DROP TABLE IF EXISTS `chest_instance_rewards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `chest_instance_rewards` (
  `instance_id` int(11) NOT NULL,
  `reward_type` enum('gil','item','key') NOT NULL,
  `reward_item_id` int(11) DEFAULT NULL,
  `reward_key_item_id` int(11) DEFAULT NULL,
  `reward_amount` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`instance_id`,`reward_type`),
  KEY `reward_item_id` (`reward_item_id`),
  KEY `reward_key_item_id` (`reward_key_item_id`),
  CONSTRAINT `chest_instance_rewards_ibfk_1` FOREIGN KEY (`instance_id`) REFERENCES `treasure_chest_instances` (`instance_id`) ON DELETE CASCADE,
  CONSTRAINT `chest_instance_rewards_ibfk_2` FOREIGN KEY (`reward_item_id`) REFERENCES `items` (`item_id`) ON DELETE SET NULL,
  CONSTRAINT `chest_instance_rewards_ibfk_3` FOREIGN KEY (`reward_key_item_id`) REFERENCES `key_items` (`key_item_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chest_instance_rewards`
--

LOCK TABLES `chest_instance_rewards` WRITE;
/*!40000 ALTER TABLE `chest_instance_rewards` DISABLE KEYS */;
INSERT INTO `chest_instance_rewards` VALUES
(1,'key',7,NULL,1);
/*!40000 ALTER TABLE `chest_instance_rewards` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `class_abilities`
--

DROP TABLE IF EXISTS `class_abilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `class_abilities` (
  `class_id` int(11) NOT NULL,
  `ability_id` int(11) NOT NULL,
  `unlock_level` int(11) DEFAULT 1,
  PRIMARY KEY (`class_id`,`ability_id`),
  KEY `ability_id` (`ability_id`),
  KEY `unlock_level` (`unlock_level`),
  CONSTRAINT `class_abilities_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`class_id`) ON DELETE CASCADE,
  CONSTRAINT `class_abilities_ibfk_2` FOREIGN KEY (`ability_id`) REFERENCES `abilities` (`ability_id`) ON DELETE CASCADE,
  CONSTRAINT `class_abilities_ibfk_3` FOREIGN KEY (`unlock_level`) REFERENCES `levels` (`level`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `class_abilities`
--

LOCK TABLES `class_abilities` WRITE;
/*!40000 ALTER TABLE `class_abilities` DISABLE KEYS */;
INSERT INTO `class_abilities` VALUES
(1,7,1),
(1,14,1),
(2,7,1),
(2,10,1),
(3,38,1),
(3,39,1),
(3,40,1),
(4,9,1),
(4,50,1),
(5,33,1),
(5,34,1),
(5,35,1),
(6,6,1),
(6,7,1),
(8,1,1),
(9,2,1),
(9,3,1),
(9,12,1),
(10,13,1),
(10,37,1),
(11,88,1),
(12,1,1),
(12,2,1),
(12,3,1),
(12,12,1),
(1,15,2),
(1,41,2),
(7,52,2),
(9,17,2),
(9,28,2),
(9,37,2),
(4,48,3),
(7,9,3),
(8,11,3),
(9,19,3),
(11,89,3),
(7,53,4),
(9,21,4),
(1,16,5),
(3,47,5),
(4,51,5),
(5,32,5),
(6,9,5),
(8,4,5),
(9,5,5),
(9,36,5),
(10,31,5),
(11,90,5),
(1,42,6),
(3,45,10),
(5,17,10),
(7,33,10),
(8,26,10),
(8,28,10),
(9,23,10),
(10,23,10),
(1,43,15),
(3,44,15),
(5,25,15),
(8,27,15),
(9,18,15),
(9,20,15),
(9,22,15),
(3,43,20),
(3,49,20),
(9,24,20);
/*!40000 ALTER TABLE `class_abilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `class_trances`
--

DROP TABLE IF EXISTS `class_trances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `class_trances` (
  `trance_id` int(11) NOT NULL AUTO_INCREMENT,
  `class_id` int(11) NOT NULL,
  `trance_name` varchar(32) NOT NULL,
  `duration_turns` int(11) NOT NULL,
  PRIMARY KEY (`trance_id`),
  KEY `class_id` (`class_id`),
  CONSTRAINT `class_trances_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`class_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `class_trances`
--

LOCK TABLES `class_trances` WRITE;
/*!40000 ALTER TABLE `class_trances` DISABLE KEYS */;
INSERT INTO `class_trances` VALUES
(1,1,'Braver',15),
(2,2,'Berserk',15),
(3,3,'SpellBlade',15),
(4,4,'Mug',15),
(5,5,'Mace',15),
(6,6,'Jump',15),
(7,7,'Ensemble',15),
(8,8,'Dbl White',15),
(9,9,'Dbl Black',15),
(10,10,'Enviro',15),
(11,11,'Eat',15),
(12,12,'Esper',15);
/*!40000 ALTER TABLE `class_trances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `classes`
--

DROP TABLE IF EXISTS `classes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `classes` (
  `class_id` int(11) NOT NULL AUTO_INCREMENT,
  `class_name` varchar(50) NOT NULL,
  `description` text DEFAULT NULL,
  `base_hp` int(11) DEFAULT 100,
  `base_attack` int(11) DEFAULT 10,
  `base_magic` int(11) DEFAULT 10,
  `base_mp` int(11) DEFAULT 0,
  `base_defense` int(11) DEFAULT 5,
  `base_magic_defense` int(11) DEFAULT 5,
  `base_accuracy` int(11) DEFAULT 95,
  `base_evasion` int(11) DEFAULT 5,
  `base_speed` int(11) DEFAULT 10,
  `image_url` varchar(255) DEFAULT NULL,
  `creator_id` bigint(20) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `atb_max` int(11) DEFAULT 5,
  PRIMARY KEY (`class_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `classes`
--

LOCK TABLES `classes` WRITE;
/*!40000 ALTER TABLE `classes` DISABLE KEYS */;
INSERT INTO `classes` VALUES
(1,'Warrior','A sturdy fighter with strong physical attacks.',600,40,10,0,5,1,99,1,10,'https://cdn.discordapp.com/attachments/1362832151485354065/1364778448379318442/war.gif?ex=680c39fa&is=680ae87a&hm=80c89e0290ea5ad2432f2d9b265df190741f94309c2bca981ad1885af90671c4&',NULL,'2025-03-31 07:40:47',5),
(2,'Berserker','A savage fighter who channels uncontrollable fury.',600,45,10,0,5,1,99,1,10,'https://cdn.discordapp.com/attachments/1362832151485354065/1365296689379938355/Berserker.gif?ex=680ccb20&is=680b79a0&hm=aa06cfa2c7fb2fb30ffe9e4991d2dda0d4f9420587656a0ddc61b192372ad067&',NULL,'2025-04-03 12:05:45',5),
(3,'Mystic Knight','A hybrid fighter that fuses magic to their blade.',500,40,15,0,5,1,99,1,10,'https://cdn.discordapp.com/attachments/1362832151485354065/1365296718815432724/mystic.gif?ex=680ccb27&is=680b79a7&hm=3f8ad9a2b215496adbc6c0dfd328a9e30621c73e292c40f0fd5ebfb0025bd910&',NULL,'2025-04-03 12:05:45',5),
(4,'Thief','A quick fighter who excels at stealing items.',500,45,10,0,5,1,99,1,10,'https://cdn.discordapp.com/attachments/1362832151485354065/1365296784301363303/thief.gif?ex=680ccb37&is=680b79b7&hm=34ee2d981b968e6de51e52e85c51b3c16ed4ac71974df3ada3f305603d95b59a&',NULL,'2025-03-31 07:40:47',5),
(5,'Green Mage','A powerful mage that manipulates time and space magics.',500,20,20,80,5,1,99,1,10,NULL,NULL,'2025-03-31 07:40:47',5),
(6,'Dragoon','A lancer who can jump high and strike down foes.',500,40,10,0,5,1,99,1,10,NULL,NULL,'2025-03-31 07:40:47',5),
(7,'Bard','A ranged attacker wielding a bow and musical influence.',500,45,20,40,5,1,99,1,10,NULL,NULL,'2025-04-03 12:05:45',5),
(8,'White Mage','A healer who uses holy magic to restore and protect.',500,15,20,120,5,1,99,1,10,'https://cdn.discordapp.com/attachments/1362832151485354065/1365296761723158538/whitemage.gif?ex=680ccb31&is=680b79b1&hm=cd94aeb45272086aac0e5c40507390e5738ef9ee419634a7eded75bf67ea91be&',NULL,'2025-04-03 12:05:45',5),
(9,'Black Mage','A mage who uses destructive elemental spells.',500,15,25,120,5,1,99,1,10,'https://cdn.discordapp.com/attachments/1362832151485354065/1364772285873127434/blm.gif?ex=680c343d&is=680ae2bd&hm=c3ce479bfd4cd9152348f3bf1d114ce29a63c7c04ac42c7d3ad845ab6bf51eda&',NULL,'2025-04-03 12:05:45',5),
(10,'Geomancer','A sorcerer using environmental/elemental attacks.',500,15,20,80,5,1,99,1,10,'https://cdn.discordapp.com/attachments/1362832151485354065/1372019632139145237/out.gif?ex=6825405b&is=6823eedb&hm=b0c22f7902cc76c50ce038d3c74dc16559a02e5e3d4262b5173592491bce32e6&',NULL,'2025-04-03 12:05:45',5),
(11,'Gun Mage','A mage clad in blue armor who holds a magic-infused pistol.',600,30,15,60,5,1,99,1,10,'https://cdn.discordapp.com/attachments/1362832151485354065/1372162446311165983/out.gif?ex=6825c55c&is=682473dc&hm=1e03aac8f24a02d80ee1f48c84a204d43207a75b55259d5bb8c461bb7af6f35e&',NULL,'2025-04-03 12:05:45',5),
(12,'Summoner','A mage who bonds with Eidolons and calls them to battle.',480,15,20,160,5,1,99,1,10,NULL,NULL,'2025-07-01 05:00:00',5);
/*!40000 ALTER TABLE `classes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `crystal_templates`
--

DROP TABLE IF EXISTS `crystal_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `crystal_templates` (
  `template_id` int(11) NOT NULL AUTO_INCREMENT,
  `element_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`template_id`),
  KEY `element_id` (`element_id`),
  CONSTRAINT `crystal_templates_ibfk_1` FOREIGN KEY (`element_id`) REFERENCES `elements` (`element_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `crystal_templates`
--

LOCK TABLES `crystal_templates` WRITE;
/*!40000 ALTER TABLE `crystal_templates` DISABLE KEYS */;
INSERT INTO `crystal_templates` VALUES
(1,1,'Red Crystal Shard','The room\'s illusion shifts...\n\nA glowing red crystal shard appears, what should you do?','https://cdn.discordapp.com/attachments/1362832151485354065/1384704817330393269/firecrystal.png?ex=6853665b&is=685214db&hm=0b49ddc1370d2b2f91a408bbbbe76fb0d5d5723c202e53db14e52322d77fbe98&','2025-06-18 06:33:11'),
(2,2,'Light-Blue Crystal Shard','The room\'s illusion shifts...\n\nA glowing light-blue crystal shard appears, what should you do?','https://cdn.discordapp.com/attachments/1362832151485354065/1384703341178654820/icecrystal.png?ex=685364fb&is=6852137b&hm=5f7940f58527f53be967d56a159f00916417199bc314f6eb12bb81bd4b0cf59e&','2025-06-18 06:34:12'),
(3,3,'Light-Pink Crystal Shard','The room\'s illusion shifts...\n\nA glowing light-pink crystal shard appears, what should you do?','https://cdn.discordapp.com/attachments/1362832151485354065/1384707943659995256/holycrystal.png?ex=68536944&is=685217c4&hm=041a02f83ce5b5103e2ce97b6c2e2028473ccdbe2276980fcdb53f119fdd77f0&','2025-06-18 06:35:39'),
(4,4,'Black Crystal Shard','The room\'s illusion shifts...\n\nA glowing light-pink crystal shard appears, what should you do?','https://cdn.discordapp.com/attachments/1362832151485354065/1384709533502279690/deathcrystal.png?ex=68536abf&is=6852193f&hm=c07c4db1ffa345b5c7817741d9294fbdc4540c88f21b5f628b6b09705c0610fd&','2025-06-18 06:41:56'),
(5,5,'Grey Crystal Shard','The room\'s illusion shifts...\n\nA glowing grey crystal shard appears, what should you do?','https://cdn.discordapp.com/attachments/1362832151485354065/1384703288770826380/aircrystal.png?ex=685364ee&is=6852136e&hm=12e5cc4fbe5b756c046c7d8ccaf0c82acfe55d7f99a22cdb4d14404471ba4cfa&','2025-06-18 06:41:56'),
(6,6,'Purple Crystal Shard','The room\'s illusion shifts...\n\nA glowing purple crystal shard appears, what should you do?','https://cdn.discordapp.com/attachments/1362832151485354065/1384704317050589307/lightningcrystal.png?ex=685365e3&is=68521463&hm=d9668f3b00e6fdcb3d5251fef5e16940985a9741240efee914ebf599fc5befd6&','2025-06-18 06:41:56'),
(7,7,'Blue Crystal Shard','The room\'s illusion shifts...\n\nA glowing blue crystal shard appears, what should you do?','https://cdn.discordapp.com/attachments/1362832151485354065/1384701852913897633/watercrystal.png?ex=68536398&is=68521218&hm=004d052a414f1caef751389b09a99a8eff5a1eec84863f97208584836b31e0e0&','2025-06-18 06:41:56'),
(8,8,'Green Crystal Shard','The room\'s illusion shifts...\n\nA glowing green crystal shard appears, what should you do?','https://cdn.discordapp.com/attachments/1362832151485354065/1384701828759031838/earthcrystal.png?ex=68536392&is=68521212&hm=345ac8cdf68e2057c36b8ed4d1a6290f51fe6e227d986320fe19ff0caac20dce&','2025-06-18 06:41:56');
/*!40000 ALTER TABLE `crystal_templates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `difficulties`
--

DROP TABLE IF EXISTS `difficulties`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `difficulties` (
  `difficulty_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `width` int(11) NOT NULL,
  `height` int(11) NOT NULL,
  `min_floors` int(11) NOT NULL,
  `max_floors` int(11) NOT NULL,
  `min_rooms` int(11) NOT NULL,
  `enemy_chance` float NOT NULL,
  `npc_count` int(11) NOT NULL,
  `basement_chance` float NOT NULL DEFAULT 0,
  `basement_min_rooms` int(11) NOT NULL DEFAULT 0,
  `basement_max_rooms` int(11) NOT NULL DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `shops_per_floor` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`difficulty_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `difficulties`
--

LOCK TABLES `difficulties` WRITE;
/*!40000 ALTER TABLE `difficulties` DISABLE KEYS */;
INSERT INTO `difficulties` VALUES
(1,'Easy',10,10,2,2,80,0.2,2,0.1,20,40,'2025-03-31 07:40:47',2),
(2,'Medium',10,10,2,3,80,0.25,3,0.15,20,40,'2025-03-31 07:40:47',2),
(3,'Hard',12,12,2,3,100,0.3,3,0.2,30,50,'2025-03-31 07:40:47',1),
(4,'Crazy Catto',12,12,3,4,125,0.4,3,0.25,40,60,'2025-03-31 07:40:47',1);
/*!40000 ALTER TABLE `difficulties` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `eidolon_abilities`
--

DROP TABLE IF EXISTS `eidolon_abilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eidolon_abilities` (
  `eidolon_id` int(11) NOT NULL,
  `ability_id` int(11) NOT NULL,
  `unlock_level` int(11) DEFAULT 1,
  PRIMARY KEY (`eidolon_id`,`ability_id`),
  KEY `ability_id` (`ability_id`),
  KEY `unlock_level` (`unlock_level`),
  CONSTRAINT `eidolon_abilities_ibfk_1` FOREIGN KEY (`eidolon_id`) REFERENCES `eidolons` (`eidolon_id`) ON DELETE CASCADE,
  CONSTRAINT `eidolon_abilities_ibfk_2` FOREIGN KEY (`ability_id`) REFERENCES `abilities` (`ability_id`) ON DELETE CASCADE,
  CONSTRAINT `eidolon_abilities_ibfk_3` FOREIGN KEY (`unlock_level`) REFERENCES `levels` (`level`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `eidolon_abilities`
--

LOCK TABLES `eidolon_abilities` WRITE;
/*!40000 ALTER TABLE `eidolon_abilities` DISABLE KEYS */;
INSERT INTO `eidolon_abilities` VALUES
(1,2,1),
(1,201,1),
(2,3,1),
(2,202,1),
(3,12,1),
(3,203,1),
(1,17,5),
(2,19,5),
(3,21,5),
(1,18,10),
(2,20,10),
(3,22,10);
/*!40000 ALTER TABLE `eidolon_abilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `eidolons`
--

DROP TABLE IF EXISTS `eidolons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eidolons` (
  `eidolon_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `enemy_id` int(11) NOT NULL,
  `required_level` int(11) NOT NULL DEFAULT 1,
  `base_hp` int(11) DEFAULT 100,
  `base_attack` int(11) DEFAULT 10,
  `base_magic` int(11) DEFAULT 10,
  `base_defense` int(11) DEFAULT 5,
  `base_magic_defense` int(11) DEFAULT 5,
  `base_accuracy` int(11) DEFAULT 95,
  `base_evasion` int(11) DEFAULT 5,
  `base_speed` int(11) DEFAULT 10,
  `summon_mp_cost` int(11) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`eidolon_id`),
  KEY `enemy_id` (`enemy_id`),
  CONSTRAINT `eidolons_ibfk_1` FOREIGN KEY (`enemy_id`) REFERENCES `enemies` (`enemy_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `eidolons`
--

LOCK TABLES `eidolons` WRITE;
/*!40000 ALTER TABLE `eidolons` DISABLE KEYS */;
INSERT INTO `eidolons` VALUES
(1,'Ifrit','A fiery Eidolon bound to the Cloister of Flames.',101,5,1500,80,100,50,20,8,95,5,50,'2025-07-01 05:00:00'),
(2,'Shiva','A crystalline Eidolon bound to the Cloister of Frost.',102,8,1500,80,100,50,22,10,95,6,50,'2025-07-01 05:00:00'),
(3,'Ramuh','A stormy Eidolon bound to the Cloister of Storms.',103,12,1500,80,100,50,24,10,95,6,50,'2025-07-01 05:00:00');
/*!40000 ALTER TABLE `eidolons` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `element_oppositions`
--

DROP TABLE IF EXISTS `element_oppositions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `element_oppositions` (
  `opposition_id` int(11) NOT NULL AUTO_INCREMENT,
  `element_id` int(11) NOT NULL,
  `opposing_element_id` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`opposition_id`),
  UNIQUE KEY `unique_element_opposition` (`element_id`),
  KEY `opposing_element_id` (`opposing_element_id`),
  CONSTRAINT `element_oppositions_ibfk_1` FOREIGN KEY (`element_id`) REFERENCES `elements` (`element_id`) ON DELETE CASCADE,
  CONSTRAINT `element_oppositions_ibfk_2` FOREIGN KEY (`opposing_element_id`) REFERENCES `elements` (`element_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `element_oppositions`
--

LOCK TABLES `element_oppositions` WRITE;
/*!40000 ALTER TABLE `element_oppositions` DISABLE KEYS */;
INSERT INTO `element_oppositions` VALUES
(1,1,2,'2025-12-20 16:34:38'),
(2,2,1,'2025-12-20 16:34:38'),
(3,3,4,'2025-12-20 16:34:38'),
(4,4,3,'2025-12-20 16:34:38'),
(5,5,8,'2025-12-20 16:34:38'),
(6,6,7,'2025-12-20 16:34:38'),
(7,7,6,'2025-12-20 16:34:38'),
(8,8,5,'2025-12-20 16:34:38');
/*!40000 ALTER TABLE `element_oppositions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `elements`
--

DROP TABLE IF EXISTS `elements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `elements` (
  `element_id` int(11) NOT NULL AUTO_INCREMENT,
  `element_name` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`element_id`),
  UNIQUE KEY `element_name` (`element_name`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `elements`
--

LOCK TABLES `elements` WRITE;
/*!40000 ALTER TABLE `elements` DISABLE KEYS */;
INSERT INTO `elements` VALUES
(1,'Fire','2025-03-31 07:40:47'),
(2,'Ice','2025-03-31 07:40:47'),
(3,'Holy','2025-03-31 07:40:47'),
(4,'Death','2025-03-31 07:40:47'),
(5,'Air','2025-03-31 07:40:47'),
(6,'Lightning','2025-06-18 02:39:35'),
(7,'Water','2025-06-18 02:39:35'),
(8,'Earth','2025-06-18 06:38:26');
/*!40000 ALTER TABLE `elements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `enemies`
--

DROP TABLE IF EXISTS `enemies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `enemies` (
  `enemy_id` int(11) NOT NULL AUTO_INCREMENT,
  `enemy_name` varchar(50) NOT NULL,
  `role` enum('normal','miniboss','boss','eidolon') NOT NULL DEFAULT 'normal',
  `description` text DEFAULT NULL,
  `hp` int(11) NOT NULL,
  `max_hp` int(11) NOT NULL,
  `attack_power` int(11) DEFAULT 10,
  `defense` int(11) DEFAULT 5,
  `magic_power` int(11) DEFAULT 10,
  `magic_defense` int(11) DEFAULT 5,
  `accuracy` int(11) DEFAULT 95,
  `evasion` int(11) DEFAULT 5,
  `difficulty` varchar(50) DEFAULT NULL,
  `abilities` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`abilities`)),
  `image_url` varchar(255) DEFAULT NULL,
  `spawn_chance` float DEFAULT 0.5,
  `gil_drop` int(11) DEFAULT NULL,
  `xp_reward` int(11) DEFAULT NULL,
  `loot_item_id` int(11) DEFAULT NULL,
  `loot_quantity` int(11) DEFAULT 1,
  `creator_id` bigint(20) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `atb_max` int(11) DEFAULT 5,
  PRIMARY KEY (`enemy_id`),
  KEY `loot_item_id` (`loot_item_id`),
  CONSTRAINT `enemies_ibfk_1` FOREIGN KEY (`loot_item_id`) REFERENCES `items` (`item_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enemies`
--

LOCK TABLES `enemies` WRITE;
/*!40000 ALTER TABLE `enemies` DISABLE KEYS */;
INSERT INTO `enemies` VALUES
(1,'Behemoth','normal','large, purple, canine-esque creature...',100,100,15,10,10,5,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362833225860382731/behemoth.png?ex=680db819&is=680c6699&hm=f09b8b78e76629b607f0aec017f5aef75c003a1965508701c7b7de48b5279dd7&',0.3,100,75,1,1,NULL,'2025-03-31 12:40:47',5),
(2,'Ghost','normal','pale, translucent, or wispy being...',50,50,10,10,10,5,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362833226606973221/ghost.png?ex=680db819&is=680c6699&hm=6e400e0649442964e4ac24e7dc2b0a6fd351f4557c611e85cce5ecf4d6a1e658&',0.3,50,50,3,1,NULL,'2025-03-31 12:40:47',5),
(3,'Drake','normal','An ancient creature with scales and fangs, said to be extinct for over 1,000 years.',200,200,15,10,10,10,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114639914045480/drake.png?ex=683082ce&is=682f314e&hm=92fdeabf72b3026f912674b0faa2f98bf993aea384119831b63492d607c84d3e&',0.1,150,150,1,1,NULL,'2025-03-31 12:40:47',5),
(4,'Larva','normal','A glowing entity capable of casting higher magics.',300,300,12,10,15,12,99,1,'Hard',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114662240325712/larva.png?ex=683082d3&is=682f3153&hm=9d8c16343ea85757895cbd6578e0f67d8e9aa474a7ee0ca0e812ca13b820f719&',0.2,200,200,5,1,NULL,'2025-03-31 12:40:47',5),
(5,'Black Flan','normal','A Gelatinous creature resistant to physical attacks.',200,200,11,15,11,5,99,1,'Medium',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362835170721534023/blackflan.png?ex=6803d6a8&is=68028528&hm=ee330fb7a2269de429cf44562580eb3646beff4a8de4cc2a6bc73ae4cdd930ba&',0.2,200,250,1,1,NULL,'2025-03-31 12:40:47',5),
(6,'Nightmare','normal','You feel a sudden wave of fear as the dark shrouded creature approaches...',125,125,20,10,10,5,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362835169949646998/nightmare_elemental.png?ex=680db9e8&is=680c6868&hm=66d12f806890019bad61635b0f304bc9c7acbb56128c279c515543e9066e8811&',0.1,125,150,3,1,NULL,'2025-04-10 06:20:32',5),
(7,'Tonberry Chef','normal','A creature said to be only in legend. It seems to like cooking, but where did it get that knife and chef\'s hat? Also VERY big.',250,250,20,10,10,6,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362833225033977996/tonberry_chef.png?ex=680db819&is=680c6699&hm=f8769254ee0417a70fb677d9e885764572d3673c194953cb7acc617d54c66df9&',0.1,150,110,1,1,NULL,'2025-04-10 06:20:32',5),
(8,'Overgrown Tonberry','normal','A creature said to be only in legend. Also VERY big.',200,200,10,10,10,5,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362833224136524030/overgrown_tonberry.png?ex=680db818&is=680c6698&hm=0304508b1d30e458dc4b931d10a0808d57570119961a142934061f226bcc0d1c&',0.3,75,90,1,1,NULL,'2025-03-31 12:40:47',5),
(9,'Black Flan','normal','A Gelatinous creature resistant to physical attacks.',160,160,15,15,12,2,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362835170721534023/blackflan.png?ex=6803d6a8&is=68028528&hm=ee330fb7a2269de429cf44562580eb3646beff4a8de4cc2a6bc73ae4cdd930ba&',0.5,80,80,1,1,NULL,'2025-04-17 08:03:02',5),
(10,'Bomb','normal','A ball of everlasting embers growing hotter as the enemy enrages. Watch out for it\'s self-destruct.',125,125,12,10,12,5,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362835171476377720/bombenemy.png?ex=6803d6a9&is=68028529&hm=0b67669b87b609a9e767920525d23dc9d224d1fedcb245154ada75b961905d6e&',0.5,80,80,1,1,NULL,'2025-04-17 08:03:02',5),
(11,'Chimera','normal','A beast taking on three forms, each having it\'s own abilities.',200,200,20,11,13,10,99,1,'Hard',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362835172298592508/chimera.png?ex=6803d6a9&is=68028529&hm=c207c28cc8df7b77ee82552ce183d27c2161576dcaff80cf08cdae7a98e95df6&',0.5,120,150,3,1,NULL,'2025-04-17 08:03:02',5),
(12,'Clay Golem','normal','A large being said to exist as the result of a sorcerer\'s curse. Legend states they are the last remnants of a large mining caravan.',125,125,15,10,11,5,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362835173539840062/claygolem.png?ex=6803d6a9&is=68028529&hm=258bf6843e232975707bbc8f1a65581f217007fb6154954cc3774454ee06018e&',0.5,100,120,1,1,NULL,'2025-04-17 08:03:02',5),
(13,'Ghast','normal','A large fiend with deformed limbs and humanoid features, it seems to be branded with a symbol of sorts.',150,150,18,12,11,6,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362835175716683907/ghast.png?ex=6803d6aa&is=6802852a&hm=711d53e92c6df922e46e0f090427db41faad6cd07aecd22e5604dfc1ab53af5f&',0.5,175,150,3,1,NULL,'2025-04-17 08:03:02',5),
(14,'Iron Giant','normal','A giant knight clad in Iron armor. It is known for having high defense.',275,275,25,20,12,5,99,1,'Medium',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362835176635240458/irongiant.png?ex=6803d6aa&is=6802852a&hm=66b16d26c72317c93fcaf313b1f8dc3cdbf127853d77dec2ce3e60160eaebaac&',0.5,200,300,1,1,NULL,'2025-04-17 08:03:02',5),
(15,'Marlboro','normal','A smelly creature with large sharp teeth, long vine-like tentacles, and multiple eyes.',175,175,17,12,12,5,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362835177486680437/marlboro.png?ex=6803d6aa&is=6802852a&hm=1c750b1405bda87627ad13f8d16b3f717c1f0298afdac7a3d2387bac69724363&',0.5,150,150,1,1,NULL,'2025-04-17 08:03:02',5),
(16,'Mimic','miniboss','A small chest bearing fangs and teeth.',500,500,20,20,15,10,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1365786181417177148/2.png?ex=680f3bc0&is=680dea40&hm=cfad9ebbb97d24ec72185a1f248403001fcb9fbc6e8f3f8d463fc971d5c20bb8&',0.2,500,2000,6,1,NULL,'2025-04-26 20:26:50',5),
(17,'Lightning Elemental','boss','You hear static crackle in the air...',500,500,20,20,20,20,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1366755651786637312/lightning_elemental.png?ex=681219e4&is=6810c864&hm=8c9364bff4b0760c66ac1b1d516666b830d550c9bc75a82b85d829d1c0aa7aa1&',0.2,500,3000,8,1,NULL,'2025-04-26 20:26:50',5),
(18,'Agares','normal','A goblin creature that appears to use magic and is dressed in unfamiliar garb.',200,200,10,10,12,6,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114561799192766/Agares.png?ex=683082bb&is=682f313b&hm=bcec9bdaf61b08d27897db07918df65d15cd8d25ead882e0cd4d792b9376a99d&',0.1,200,175,5,1,NULL,'2025-05-22 19:42:26',5),
(19,'Cactuar','normal','An evasive cactus species that is known to attack and run, watch our for it\'s Needles!',200,200,15,12,10,7,99,2,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114595626389514/Cactuar.png?ex=683082c3&is=682f3143&hm=6dc61cc626160c8ed9d1619142eb319365330b98641bd2e9db5359c4fef1c373&',0.1,150,150,1,1,NULL,'2025-05-22 19:42:26',5),
(20,'Demon Eye','normal','A floating creature with one eye and bat like wings.',220,220,13,10,13,6,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114610457313414/demoneyeball.png?ex=683082c7&is=682f3147&hm=e2512d5ab06077b428c84552b2d9ce68c3c2c58d010a4744c3ea9819b2b1174a&',0.1,110,150,1,1,NULL,'2025-05-22 19:42:26',5),
(21,'Demon Eye','normal','A floating creature with one eye and bat like wings.',220,220,13,10,13,6,99,1,'Medium',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114610457313414/demoneyeball.png?ex=683082c7&is=682f3147&hm=e2512d5ab06077b428c84552b2d9ce68c3c2c58d010a4744c3ea9819b2b1174a&',0.1,110,150,1,1,NULL,'2025-05-22 19:42:26',5),
(22,'Larva','normal','A glowing entity capable of casting higher magics.',250,250,10,10,12,6,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114662240325712/larva.png?ex=683082d3&is=682f3153&hm=9d8c16343ea85757895cbd6578e0f67d8e9aa474a7ee0ca0e812ca13b820f719&',0.1,200,180,5,1,NULL,'2025-05-22 19:42:26',5),
(23,'Black Waltz','miniboss','A mage resembling those from stories of the Dark Era of Alexandria. Where did it come from? What or who could it be searching for?',600,600,10,10,13,12,99,1,'Easy',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114690589364266/blackwaltz.png?ex=683082da&is=682f315a&hm=dd33c631faee48b90bedb3c64c62b15b1b5dc339324507287cf396b0eb08f724&',0.1,500,2200,4,1,NULL,'2025-05-22 19:42:26',5),
(24,'Black Waltz','miniboss','A mage resembling those from stories of the Dark Era of Alexandria. Where did it come from? What or who could it be searching for?',800,800,11,11,14,13,99,1,'Medium',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114690589364266/blackwaltz.png?ex=683082da&is=682f315a&hm=dd33c631faee48b90bedb3c64c62b15b1b5dc339324507287cf396b0eb08f724&',0.1,500,2200,4,1,NULL,'2025-05-22 19:42:26',5),
(25,'Drake','normal','An ancient creature with scales and fangs, said to be extinct for over 1,000 years.',300,300,15,10,10,10,99,1,'Medium',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114639914045480/drake.png?ex=683082ce&is=682f314e&hm=92fdeabf72b3026f912674b0faa2f98bf993aea384119831b63492d607c84d3e&',0.1,150,150,5,1,NULL,'2025-03-31 12:40:47',5),
(26,'Cactuar','normal','An evasive cactus species that is known to attack and run, watch our for it\'s Needles!',300,300,15,13,11,8,99,1,'Medium',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1375114595626389514/Cactuar.png?ex=683082c3&is=682f3143&hm=6dc61cc626160c8ed9d1619142eb319365330b98641bd2e9db5359c4fef1c373&',0.1,220,200,5,1,NULL,'2025-05-22 19:44:44',5),
(101,'Ifrit','eidolon','A blazing Eidolon wreathed in infernal flames.',1200,1200,25,18,30,20,99,5,'Summoner',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1451937077259272273/730fb195-cea1-4183-8ef4-f2677b1eb88e.png?ex=6947fd46&is=6946abc6&hm=bd42838fc0ee3081d00e2ec5567833f34716270c3c9e332c54c1ad00e237b190&',0,500,800,NULL,1,NULL,'2025-07-01 05:00:00',6),
(102,'Shiva','eidolon','A frigid Eidolon whose breath freezes the air.',1300,1300,22,18,32,22,99,6,'Summoner',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1451938841089802391/e0b5b388-de0f-4a0e-a34d-adbae339711d.png?ex=6947feeb&is=6946ad6b&hm=4be5a3a201950ce527ebbdbbed9f6745cbc45ef515b2ca59a0252d693124921c&',0,600,900,NULL,1,NULL,'2025-07-01 05:00:00',6),
(103,'Ramuh','eidolon','A stormbound Eidolon crackling with lightning.',1400,1400,24,20,34,24,99,6,'Summoner',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1451943284728664064/d9544aeb-1d50-4766-b2fa-7dc21a8b4aaf.png?ex=6948030e&is=6946b18e&hm=551008eb7439d8ea3a128d0e42394029bdadd82f4c90b3ea514286185ea67bbd&',0,700,1000,NULL,1,NULL,'2025-07-01 05:00:00',6);
/*!40000 ALTER TABLE `enemies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `enemy_abilities`
--

DROP TABLE IF EXISTS `enemy_abilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `enemy_abilities` (
  `enemy_id` int(11) NOT NULL,
  `ability_id` int(11) NOT NULL,
  `weight` int(11) NOT NULL DEFAULT 1,
  `can_heal` tinyint(1) NOT NULL DEFAULT 0,
  `heal_threshold_pct` float DEFAULT NULL,
  `heal_amount_pct` float DEFAULT NULL,
  `scaling_stat` enum('attack_power','magic_power','defense') NOT NULL,
  `scaling_factor` float NOT NULL DEFAULT 0,
  `accuracy` int(11) NOT NULL DEFAULT 100,
  PRIMARY KEY (`enemy_id`,`ability_id`),
  KEY `ability_id` (`ability_id`),
  CONSTRAINT `enemy_abilities_ibfk_1` FOREIGN KEY (`enemy_id`) REFERENCES `enemies` (`enemy_id`) ON DELETE CASCADE,
  CONSTRAINT `enemy_abilities_ibfk_2` FOREIGN KEY (`ability_id`) REFERENCES `abilities` (`ability_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enemy_abilities`
--

LOCK TABLES `enemy_abilities` WRITE;
/*!40000 ALTER TABLE `enemy_abilities` DISABLE KEYS */;
INSERT INTO `enemy_abilities` VALUES
(1,2,1,0,NULL,NULL,'attack_power',1,100),
(1,7,1,0,NULL,NULL,'attack_power',1,100),
(2,2,1,0,NULL,NULL,'attack_power',1,100),
(2,7,1,0,NULL,NULL,'attack_power',1,100),
(2,9,1,0,NULL,NULL,'attack_power',1,100),
(3,15,0,0,NULL,NULL,'attack_power',1,100),
(3,35,0,0,NULL,NULL,'attack_power',1,100),
(4,17,0,0,NULL,NULL,'magic_power',1,100),
(4,19,0,0,NULL,NULL,'magic_power',1,100),
(4,21,0,0,NULL,NULL,'magic_power',1,100),
(5,10,1,0,NULL,NULL,'attack_power',1,100),
(5,12,1,0,NULL,NULL,'attack_power',1,100),
(6,12,3,0,NULL,NULL,'magic_power',1,100),
(6,21,1,0,NULL,NULL,'magic_power',1,100),
(7,17,3,0,NULL,NULL,'magic_power',1,100),
(7,91,1,0,NULL,NULL,'attack_power',1,100),
(8,2,3,0,NULL,NULL,'magic_power',1,100),
(8,91,1,0,NULL,NULL,'attack_power',1,100),
(9,17,1,0,NULL,NULL,'magic_power',1,100),
(9,19,1,0,NULL,NULL,'magic_power',1,100),
(10,2,1,0,NULL,NULL,'magic_power',1,100),
(11,17,2,0,NULL,NULL,'magic_power',1,100),
(11,19,2,0,NULL,NULL,'magic_power',1,100),
(11,21,2,0,NULL,NULL,'magic_power',1,100),
(11,23,1,0,NULL,NULL,'magic_power',1,100),
(12,1,1,1,0.15,0.15,'magic_power',1,100),
(13,16,1,0,NULL,NULL,'attack_power',1,100),
(13,31,1,0,NULL,NULL,'magic_power',1,100),
(14,1,1,1,0.25,0.15,'magic_power',1,100),
(14,14,1,0,NULL,NULL,'attack_power',1,100),
(15,36,1,0,NULL,NULL,'attack_power',1,100),
(16,2,1,0,NULL,NULL,'magic_power',1,100),
(16,3,1,0,NULL,NULL,'magic_power',1,100),
(16,12,1,0,NULL,NULL,'magic_power',1,100),
(17,21,3,0,NULL,NULL,'magic_power',1,100),
(17,22,1,0,NULL,NULL,'magic_power',1,100),
(18,2,0,0,NULL,NULL,'magic_power',1,100),
(18,3,0,0,NULL,NULL,'magic_power',1,100),
(18,12,0,0,NULL,NULL,'magic_power',1,100),
(19,92,0,0,NULL,NULL,'attack_power',0,100),
(20,2,0,0,NULL,NULL,'magic_power',1,100),
(20,35,0,0,NULL,NULL,'magic_power',1,100),
(21,17,0,0,NULL,NULL,'magic_power',1,100),
(21,30,0,0,NULL,NULL,'magic_power',1,100),
(21,36,0,0,NULL,NULL,'magic_power',1,100),
(22,1,0,1,0.2,0.15,'magic_power',1,100),
(22,2,0,0,NULL,NULL,'magic_power',1,100),
(22,3,0,0,NULL,NULL,'magic_power',1,100),
(22,12,0,0,NULL,NULL,'magic_power',1,100),
(23,4,0,0,NULL,NULL,'magic_power',1,100),
(23,17,0,0,NULL,NULL,'magic_power',1,100),
(23,19,0,0,NULL,NULL,'magic_power',1,100),
(23,21,0,0,NULL,NULL,'magic_power',1,100),
(23,26,0,1,0.2,0.5,'magic_power',1,100),
(24,17,0,0,NULL,NULL,'magic_power',1,100),
(24,19,0,0,NULL,NULL,'magic_power',1,100),
(24,21,0,0,NULL,NULL,'magic_power',1,100),
(24,24,0,0,NULL,NULL,'magic_power',1,100),
(24,26,0,1,0.3,0.5,'magic_power',1,100),
(25,15,0,0,NULL,NULL,'attack_power',1,100),
(25,36,0,0,NULL,NULL,'attack_power',1,100),
(26,7,0,0,NULL,NULL,'attack_power',1,100),
(26,30,0,0,NULL,NULL,'magic_power',1,100),
(26,93,0,0,NULL,NULL,'attack_power',1,100),
(101,18,3,0,NULL,NULL,'magic_power',1,100),
(101,201,1,0,NULL,NULL,'magic_power',1,100),
(102,20,3,0,NULL,NULL,'magic_power',1,100),
(102,202,1,0,NULL,NULL,'magic_power',1,100),
(103,22,3,0,NULL,NULL,'magic_power',1,100),
(103,203,1,0,NULL,NULL,'magic_power',1,100);
/*!40000 ALTER TABLE `enemy_abilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `enemy_drops`
--

DROP TABLE IF EXISTS `enemy_drops`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `enemy_drops` (
  `enemy_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `drop_chance` float NOT NULL,
  `min_qty` int(11) DEFAULT 1,
  `max_qty` int(11) DEFAULT 1,
  PRIMARY KEY (`enemy_id`,`item_id`),
  KEY `item_id` (`item_id`),
  CONSTRAINT `enemy_drops_ibfk_1` FOREIGN KEY (`enemy_id`) REFERENCES `enemies` (`enemy_id`) ON DELETE CASCADE,
  CONSTRAINT `enemy_drops_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enemy_drops`
--

LOCK TABLES `enemy_drops` WRITE;
/*!40000 ALTER TABLE `enemy_drops` DISABLE KEYS */;
INSERT INTO `enemy_drops` VALUES
(1,1,0.5,1,1),
(2,3,0.25,1,1),
(4,1,0.25,1,1);
/*!40000 ALTER TABLE `enemy_drops` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `enemy_resistances`
--

DROP TABLE IF EXISTS `enemy_resistances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `enemy_resistances` (
  `enemy_id` int(11) NOT NULL,
  `element_id` int(11) NOT NULL,
  `resistance` int(11) NOT NULL,
  `relation` enum('weak','resist','absorb','immune','normal') NOT NULL DEFAULT 'normal',
  `multiplier` float NOT NULL DEFAULT 1,
  PRIMARY KEY (`enemy_id`,`element_id`),
  KEY `element_id` (`element_id`),
  CONSTRAINT `enemy_resistances_ibfk_1` FOREIGN KEY (`enemy_id`) REFERENCES `enemies` (`enemy_id`) ON DELETE CASCADE,
  CONSTRAINT `enemy_resistances_ibfk_2` FOREIGN KEY (`element_id`) REFERENCES `elements` (`element_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enemy_resistances`
--

LOCK TABLES `enemy_resistances` WRITE;
/*!40000 ALTER TABLE `enemy_resistances` DISABLE KEYS */;
INSERT INTO `enemy_resistances` VALUES
(4,1,0,'weak',1.5),
(5,3,0,'weak',1.5),
(10,1,100,'absorb',-1),
(10,2,0,'weak',1.5),
(12,1,0,'weak',1.5),
(13,6,0,'weak',1.5),
(15,1,0,'weak',1.5),
(19,1,0,'resist',0.5),
(19,7,0,'weak',1.5);
/*!40000 ALTER TABLE `enemy_resistances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `floor_room_rules`
--

DROP TABLE IF EXISTS `floor_room_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `floor_room_rules` (
  `rule_id` int(11) NOT NULL AUTO_INCREMENT,
  `difficulty_name` varchar(50) NOT NULL,
  `floor_number` int(11) DEFAULT NULL,
  `room_type` enum('safe','entrance','monster','item','shop','boss','trap','illusion','staircase_up','staircase_down','exit','locked','cloister') NOT NULL,
  `chance` float NOT NULL,
  `max_per_floor` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`rule_id`),
  KEY `difficulty_name` (`difficulty_name`),
  CONSTRAINT `floor_room_rules_ibfk_1` FOREIGN KEY (`difficulty_name`) REFERENCES `difficulties` (`name`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `floor_room_rules`
--

LOCK TABLES `floor_room_rules` WRITE;
/*!40000 ALTER TABLE `floor_room_rules` DISABLE KEYS */;
INSERT INTO `floor_room_rules` VALUES
(1,'Easy',1,'safe',0.5,80,'2025-04-25 02:03:18'),
(2,'Easy',2,'monster',0.3,10,'2025-04-25 02:03:18'),
(3,'Easy',2,'item',0.1,4,'2025-04-25 02:03:18'),
(4,'Easy',1,'staircase_down',0.05,1,'2025-04-25 02:03:18'),
(5,'Easy',2,'illusion',0.05,1,'2025-04-25 02:03:18'),
(6,'Easy',2,'safe',0.5,50,'2025-04-25 02:03:18'),
(7,'Easy',2,'shop',0.1,2,'2025-04-22 00:07:34'),
(8,'Easy',1,'illusion',0.1,3,'2025-04-22 00:33:59'),
(9,'Easy',1,'monster',0.5,60,'2025-04-22 00:07:34'),
(10,'Easy',1,'item',0.3,6,'2025-04-22 00:07:34'),
(11,'Easy',1,'shop',0.1,2,'2025-04-22 00:07:34'),
(12,'Easy',1,'exit',0,0,'2025-04-22 00:33:59'),
(13,'Easy',2,'staircase_up',0,0,'2025-04-22 00:33:59'),
(14,'Easy',1,'boss',0,0,'2025-04-22 00:33:59'),
(15,'Easy',2,'boss',0.1,1,'2025-04-22 00:33:59'),
(16,'Easy',1,'locked',0.1,3,'2025-05-25 06:57:39'),
(17,'Easy',2,'locked',0.1,3,'2025-05-25 06:57:39'),
(18,'Easy',1,'cloister',100,3,'2025-07-01 05:00:00'),
(19,'Easy',2,'cloister',0.02,1,'2025-07-01 05:00:00'),
(20,'Medium',1,'safe',0.5,50,'2025-04-25 02:03:18'),
(21,'Medium',2,'safe',0.5,50,'2025-04-25 02:03:18'),
(22,'Medium',1,'monster',0.5,70,'2025-04-22 00:07:34'),
(23,'Medium',2,'monster',0.3,10,'2025-04-25 02:03:18'),
(24,'Medium',1,'item',0.3,80,'2025-04-22 00:07:34'),
(25,'Medium',2,'item',0.1,4,'2025-04-25 02:03:18'),
(26,'Medium',1,'shop',0.1,5,'2025-04-22 00:07:34'),
(27,'Medium',2,'shop',0.1,2,'2025-04-22 00:07:34'),
(28,'Medium',1,'boss',0,0,'2025-04-22 00:33:59'),
(29,'Medium',2,'boss',0.1,1,'2025-04-22 00:33:59'),
(30,'Medium',1,'illusion',0.1,3,'2025-04-22 00:33:59'),
(31,'Medium',2,'illusion',0.05,1,'2025-04-25 02:03:18'),
(32,'Medium',1,'exit',0,0,'2025-04-22 00:33:59'),
(33,'Medium',2,'staircase_up',0,0,'2025-04-22 00:33:59'),
(34,'Medium',1,'staircase_down',0.05,1,'2025-04-25 02:03:18'),
(35,'Medium',1,'locked',0.1,3,'2025-05-25 06:57:39'),
(36,'Medium',2,'locked',0.1,3,'2025-05-25 06:57:39'),
(37,'Medium',1,'cloister',100,3,'2025-07-01 05:00:00'),
(38,'Medium',2,'cloister',0.02,1,'2025-07-01 05:00:00'),
(39,'Hard',1,'safe',0.5,80,'2025-04-25 02:03:18'),
(40,'Hard',2,'monster',0.3,10,'2025-04-25 02:03:18'),
(41,'Hard',2,'item',0.1,4,'2025-04-25 02:03:18'),
(42,'Hard',1,'staircase_down',0.05,1,'2025-04-25 02:03:18'),
(43,'Hard',2,'illusion',0.05,1,'2025-04-25 02:03:18'),
(44,'Hard',2,'safe',0.5,50,'2025-04-25 02:03:18'),
(45,'Hard',2,'shop',0.1,2,'2025-04-22 00:07:34'),
(46,'Hard',1,'illusion',0.1,3,'2025-04-22 00:33:59'),
(47,'Hard',1,'monster',0.5,60,'2025-04-22 00:07:34'),
(48,'Hard',1,'item',0.3,6,'2025-04-22 00:07:34'),
(49,'Hard',1,'shop',0.1,2,'2025-04-22 00:07:34'),
(50,'Hard',1,'exit',0,0,'2025-04-22 00:33:59'),
(51,'Hard',2,'staircase_up',0,0,'2025-04-22 00:33:59'),
(52,'Hard',1,'boss',0,0,'2025-04-22 00:33:59'),
(53,'Hard',2,'boss',0.1,1,'2025-04-22 00:33:59'),
(54,'Hard',1,'locked',0.1,3,'2025-05-25 06:57:39'),
(55,'Hard',2,'locked',0.1,3,'2025-05-25 06:57:39'),
(56,'Hard',1,'cloister',100,3,'2025-07-01 05:00:00'),
(57,'Hard',2,'cloister',0.02,1,'2025-07-01 05:00:00'),
(58,'Crazy Catto',1,'safe',0.5,50,'2025-04-25 02:03:18'),
(59,'Crazy Catto',2,'safe',0.5,50,'2025-04-25 02:03:18'),
(60,'Crazy Catto',1,'monster',0.5,70,'2025-04-22 00:07:34'),
(61,'Crazy Catto',2,'monster',0.3,10,'2025-04-25 02:03:18'),
(62,'Crazy Catto',1,'item',0.3,80,'2025-04-22 00:07:34'),
(63,'Crazy Catto',2,'item',0.1,4,'2025-04-25 02:03:18'),
(64,'Crazy Catto',1,'shop',0.1,5,'2025-04-22 00:07:34'),
(65,'Crazy Catto',2,'shop',0.1,2,'2025-04-22 00:07:34'),
(66,'Crazy Catto',1,'boss',0,0,'2025-04-22 00:33:59'),
(67,'Crazy Catto',2,'boss',0.1,1,'2025-04-22 00:33:59'),
(68,'Crazy Catto',1,'illusion',0.1,3,'2025-04-22 00:33:59'),
(69,'Crazy Catto',2,'illusion',0.05,1,'2025-04-25 02:03:18'),
(70,'Crazy Catto',1,'exit',0,0,'2025-04-22 00:33:59'),
(71,'Crazy Catto',2,'staircase_up',0,0,'2025-04-22 00:33:59'),
(72,'Crazy Catto',1,'staircase_down',0.05,1,'2025-04-25 02:03:18'),
(73,'Crazy Catto',1,'locked',0.1,3,'2025-05-25 06:57:39'),
(74,'Crazy Catto',2,'locked',0.1,3,'2025-05-25 06:57:39'),
(75,'Crazy Catto',1,'cloister',100,3,'2025-07-01 05:00:00'),
(76,'Crazy Catto',2,'cloister',0.02,1,'2025-07-01 05:00:00');
/*!40000 ALTER TABLE `floor_room_rules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `floors`
--

DROP TABLE IF EXISTS `floors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `floors` (
  `floor_id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` int(11) NOT NULL,
  `difficulty` varchar(50) DEFAULT NULL,
  `total_rooms` int(11) NOT NULL,
  `floor_number` int(11) NOT NULL,
  `is_goal_floor` tinyint(1) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`floor_id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `floors_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `floors`
--

LOCK TABLES `floors` WRITE;
/*!40000 ALTER TABLE `floors` DISABLE KEYS */;
INSERT INTO `floors` VALUES
(1,2,'Easy',80,1,0,'2025-12-21 01:14:04'),
(2,2,'Easy',80,2,1,'2025-12-21 01:14:04');
/*!40000 ALTER TABLE `floors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_events`
--

DROP TABLE IF EXISTS `game_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_events` (
  `event_id` int(11) NOT NULL AUTO_INCREMENT,
  `event_name` varchar(100) NOT NULL,
  `event_type` enum('story','battle','item','trap','special') NOT NULL,
  `effect` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`effect`)),
  `floor_id` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`event_id`),
  KEY `floor_id` (`floor_id`),
  CONSTRAINT `game_events_ibfk_1` FOREIGN KEY (`floor_id`) REFERENCES `floors` (`floor_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_events`
--

LOCK TABLES `game_events` WRITE;
/*!40000 ALTER TABLE `game_events` DISABLE KEYS */;
/*!40000 ALTER TABLE `game_events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_saves`
--

DROP TABLE IF EXISTS `game_saves`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_saves` (
  `save_id` int(11) NOT NULL AUTO_INCREMENT,
  `guild_id` bigint(20) NOT NULL,
  `save_title` varchar(100) NOT NULL,
  `save_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`save_data`)),
  `timestamp` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`save_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_saves`
--

LOCK TABLES `game_saves` WRITE;
/*!40000 ALTER TABLE `game_saves` DISABLE KEYS */;
/*!40000 ALTER TABLE `game_saves` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `high_scores`
--

DROP TABLE IF EXISTS `high_scores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `high_scores` (
  `score_id` int(11) NOT NULL AUTO_INCREMENT,
  `player_name` varchar(100) NOT NULL,
  `guild_id` bigint(20) NOT NULL,
  `player_level` int(11) DEFAULT 1,
  `player_class` varchar(50) DEFAULT NULL,
  `gil` int(11) DEFAULT 0,
  `enemies_defeated` int(11) DEFAULT 0,
  `play_time` int(11) DEFAULT 0,
  `completed_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`score_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `high_scores`
--

LOCK TABLES `high_scores` WRITE;
/*!40000 ALTER TABLE `high_scores` DISABLE KEYS */;
/*!40000 ALTER TABLE `high_scores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hub_buttons`
--

DROP TABLE IF EXISTS `hub_buttons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `hub_buttons` (
  `button_id` int(11) NOT NULL AUTO_INCREMENT,
  `embed_type` enum('main','tutorial','news') NOT NULL,
  `button_label` varchar(50) DEFAULT NULL,
  `button_custom_id` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`button_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hub_buttons`
--

LOCK TABLES `hub_buttons` WRITE;
/*!40000 ALTER TABLE `hub_buttons` DISABLE KEYS */;
/*!40000 ALTER TABLE `hub_buttons` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hub_embeds`
--

DROP TABLE IF EXISTS `hub_embeds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `hub_embeds` (
  `embed_id` int(11) NOT NULL AUTO_INCREMENT,
  `embed_type` enum('main','tutorial','news') NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `text_field` text DEFAULT NULL,
  `step_order` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`embed_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hub_embeds`
--

LOCK TABLES `hub_embeds` WRITE;
/*!40000 ALTER TABLE `hub_embeds` DISABLE KEYS */;
INSERT INTO `hub_embeds` VALUES
(1,'main',NULL,'***Step into an unexplored reality and find meaning and hidden truth behind it\'s existence.\n\nAssemble your party and compete with other players, or enter alone. \n\nChoose your class + difficulty level, and experience turn-based combat that challenges your strategy at every turn.***','https://cdn.discordapp.com/attachments/1362832151485354065/1451415058839113828/Hub.png?ex=6948115c&is=6946bfdc&hm=c48e9474e8deca66081e667a39ac8a9b1d53b2c953bf79b3c36ba0f991137684&','**AdventureBot v3.0.9 is now Live!**\n\nYou can see the current https://discord.com/channels/1337786582996095036/1376040430445133895 here.\n\n__———————————————————————————__\n**Beta Testers:**\n\nPatch 3.1 features have been partially implemented for testing.\n\nPlease see the https://discord.com/channels/1337786582996095036/1360683660365529300 channel if you come across any issues.',NULL,'2025-03-31 13:43:19'),
(2,'tutorial','Starting A Game','Simply click the **New Game** button to create a new game thread.\n\nThis will add you to the **Queue** system inside the thread, along with anyone else who wants to join.\n\n- Only the players who join the game session will see the private thread and be added to it automatically.\n\n- Up to 6 players can join via the LFG post in the Game Channel by clicking the Join button. \n\n- Additional players will be shown in the **Queue List** in the thread.\n\nWhen the creator is ready they may click **Start Game** to lock in the emount of players playing.','https://cdn.discordapp.com/attachments/1362832151485354065/1373622234865733652/Screenshot_2025-05-18_at_6.14.47_AM.png?ex=682b14e5&is=6829c365&hm=b91a3c24ed88f1f493db9a8f61473923e316e284782ab15bd565f6a82ac25966&','Coming Soon...',1,'2025-04-15 07:50:10'),
(3,'tutorial','Choose Class and Difficulty','Once the Session Creator clicks the Start Game button they can choose their class and difficulty level.\n\n- Selecting **Easy** will generate up to 2 floors with a rare chance to spawn a basement floor. In this mode most harder enemeis are removed from generation.\n\n- Choosing **Medium** difficulty will generate up to 4 floors with at least 2 and a rare chance to spawn a basement. In this mode harder enemies spawn along side easy ones during generation.\n\n- Selecting **Hard** is exactly what you think it is. With up to 4 floors and higher spawn chances on more difficult enemies and less vendor shops and item drops.\n\n- **Crazy Catto** is the most difficult of challenges and well... you\'d be a crazy catto to try it.','https://cdn.discordapp.com/attachments/1362832151485354065/1373622403455778848/Screenshot_2025-05-18_at_6.19.11_AM.png?ex=682b150d&is=6829c38d&hm=045419693ca1ecd758f7ecf5c7208ca4da321622636b908da9e15c99f97dde61&','Coming Soon...',2,'2025-04-17 08:45:05');
/*!40000 ALTER TABLE `hub_embeds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `intro_steps`
--

DROP TABLE IF EXISTS `intro_steps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `intro_steps` (
  `intro_step_id` int(11) NOT NULL AUTO_INCREMENT,
  `step_order` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`intro_step_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `intro_steps`
--

LOCK TABLES `intro_steps` WRITE;
/*!40000 ALTER TABLE `intro_steps` DISABLE KEYS */;
INSERT INTO `intro_steps` VALUES
(1,1,'An Unexpected Discovery','During what began as an ordinary raid, Sophia paused. The usual golden glow marking the entrance to familiar realms was absent, replaced instead by a strange portal shimmering with dark, translucent crystals. Curious murmurs rippled through the raid group…\n\nSophia:\n\"This... isn\'t the gate we\'re used to. Has anyone seen anything like this before?\"','https://cdn.discordapp.com/attachments/1362832151485354065/1383471362823290930/step1.png?ex=6948151c&is=6946c39c&hm=8abef3910589a84fbf6d129b79b95568a4b9b0e69a273f6807c46d02fa64f9ac&','2025-03-31 12:40:47'),
(2,2,'Mog\'s Bold Venture','As the group hesitated, Mog, the courageous Moogle companion, hovered near the mysterious entrance, eyes wide with intrigue.\n\nMog:\n\"Let me scout it out, Kupo! Moogles portal hop all the time! If there\'s trouble, I\'ll zip right back!\"\n\nSophia:\n\"Wait! Mog, we don\'t know whats on the other...\"\n\nWithout another word, Mog vanished through the darkened portal.','https://cdn.discordapp.com/attachments/1362832151485354065/1384701702602489856/Step_2.png?ex=6947f1b4&is=6946a034&hm=635a04d626ae4c6654714c73268619948e4f91fb2902147afd9cecc445023532&','2025-03-31 12:40:47'),
(3,3,'The Moogle Returns','Moments felt like hours as the group waited anxiously. Suddenly, Mog burst back through, visibly shaken.\n\nMog:\n\"It\'s... a labyrinth inside! Dark and scary, I almost got lost and I felt like something was watching me, kupo. We should not enter unprepared.\"','https://cdn.discordapp.com/attachments/1362832151485354065/1451086838453239898/step3.png?ex=6948312e&is=6946dfae&hm=28afe46a432dd1f782873b96a4cc8ebe7645a1b5cd86d56d17026b30e616442a&','2025-03-31 12:40:47'),
(4,4,'Sophia\'s Decision','Sophia nodded solemnly, her gaze steady yet filled with resolve.\n\nSophia:\n\"This discovery can\'t be ignored. Whatever lies beyond this portal demands our attention—but Mog\'s right. This will require strength, courage, and careful preparation.\"','https://cdn.discordapp.com/attachments/1362832151485354065/1451090272997085271/step4.png?ex=69483461&is=6946e2e1&hm=ee6220476fd1fe1f0effe67940daee77644f5bbf44b8cf512d1a4d03f812cd2c&','2025-04-09 19:37:27'),
(5,5,'The Call to Adventure','Returning to the Free Company house, Sophia gathered everyone, her voice clear and inspiring.\n\nSophia:\n\"Friends, we\'ve faced many challenges, but now an unknown labyrinth awaits us. The dangers are uncertain, but the potential rewards—and truths—are greater still. Will you join me in unraveling this mystery? Our next journey begins now.\"\n\nYour adventure starts here...','https://cdn.discordapp.com/attachments/1362832151485354065/1451095742214049895/step5.png?ex=69483978&is=6946e7f8&hm=3020d69fb2e9280ba2255faa2384dabcbd86b25e9cb9956ee5a441e8f34c6ed4&','2025-04-09 19:37:27');
/*!40000 ALTER TABLE `intro_steps` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `item_effects`
--

DROP TABLE IF EXISTS `item_effects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `item_effects` (
  `item_id` int(11) NOT NULL,
  `effect_id` int(11) NOT NULL,
  PRIMARY KEY (`item_id`,`effect_id`),
  KEY `effect_id` (`effect_id`),
  CONSTRAINT `item_effects_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE CASCADE,
  CONSTRAINT `item_effects_ibfk_2` FOREIGN KEY (`effect_id`) REFERENCES `status_effects` (`effect_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `item_effects`
--

LOCK TABLES `item_effects` WRITE;
/*!40000 ALTER TABLE `item_effects` DISABLE KEYS */;
/*!40000 ALTER TABLE `item_effects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `items`
--

DROP TABLE IF EXISTS `items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `items` (
  `item_id` int(11) NOT NULL AUTO_INCREMENT,
  `item_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `effect` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`effect`)),
  `type` enum('consumable','equipment','quest') NOT NULL,
  `usage_limit` int(11) DEFAULT 1,
  `price` int(11) DEFAULT 0,
  `store_stock` int(11) DEFAULT NULL,
  `target_type` enum('self','enemy','ally','any') DEFAULT 'any',
  `image_url` varchar(255) DEFAULT NULL,
  `creator_id` bigint(20) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`item_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `items`
--

LOCK TABLES `items` WRITE;
/*!40000 ALTER TABLE `items` DISABLE KEYS */;
INSERT INTO `items` VALUES
(1,'Potion','Heals 50 HP.','{\"heal\": 50}','consumable',1,100,10,'self','https://example.com/icons/potion.png',NULL,'2025-03-31 07:40:47'),
(2,'Ether','Restores 30 MP.','{\"restore_mp\": 30}','consumable',1,150,5,'self','https://example.com/icons/ether.png',NULL,'2025-03-31 07:40:47'),
(3,'Phoenix Down','Revives a fainted ally with 100 HP.','{\"heal\": 100, \"revive\": true}','consumable',1,500,2,'ally','https://example.com/icons/phoenix_down.png',NULL,'2025-03-31 07:40:47'),
(4,'Tent','Restores all HP and enables Trance for a short time.','{\"heal\": 999, \"trance\": true}','consumable',1,1200,1,'self',NULL,NULL,'2025-04-17 08:38:51'),
(5,'Hi-Potion','Heals 150 HP.','{\"heal\": 150}','consumable',1,250,3,'self',NULL,NULL,'2025-04-17 08:38:51'),
(6,'Grenade','Deals explosive damage.','{\"attack\": 120}','consumable',1,250,2,'enemy',NULL,NULL,'2025-04-17 08:40:23'),
(7,'Old Key','An old looking key.',NULL,'quest',1,0,NULL,'self',NULL,NULL,'2025-04-26 05:09:35'),
(8,'Auto-Life Magicite','A Glowing Sphere containing Life magics.','{\"revive\": true}','quest',1,0,NULL,'self',NULL,NULL,'2025-05-09 23:59:15'),
(9,'Antidote','Removes Poisoned Status',NULL,'consumable',1,0,NULL,'any','🧪',NULL,'2025-05-23 06:45:00');
/*!40000 ALTER TABLE `items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `key_items`
--

DROP TABLE IF EXISTS `key_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `key_items` (
  `key_item_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`key_item_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `key_items`
--

LOCK TABLES `key_items` WRITE;
/*!40000 ALTER TABLE `key_items` DISABLE KEYS */;
INSERT INTO `key_items` VALUES
(1,'Gold Key','A small Golden Key',NULL,'2025-04-25 08:23:30');
/*!40000 ALTER TABLE `key_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `levels`
--

DROP TABLE IF EXISTS `levels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `levels` (
  `level` int(11) NOT NULL,
  `required_exp` int(11) NOT NULL,
  `hp_increase` float NOT NULL,
  `attack_increase` float NOT NULL,
  `magic_increase` float NOT NULL,
  `defense_increase` float NOT NULL,
  `magic_defense_increase` float NOT NULL,
  `accuracy_increase` float NOT NULL,
  `evasion_increase` float NOT NULL,
  `speed_increase` float NOT NULL,
  `mp_increase` float NOT NULL DEFAULT 0,
  `unlocked_abilities` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`unlocked_abilities`)),
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `levels`
--

LOCK TABLES `levels` WRITE;
/*!40000 ALTER TABLE `levels` DISABLE KEYS */;
INSERT INTO `levels` VALUES
(1,0,0,0,0,0,0,0,0,0,0,NULL,'2025-04-08 20:00:00'),
(2,150,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-08 20:00:00'),
(3,200,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-08 20:00:00'),
(4,250,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-09 20:15:49'),
(5,300,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-09 20:15:49'),
(6,350,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-09 20:15:49'),
(7,500,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(8,600,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(9,700,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(10,900,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(11,1000,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(12,1100,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(13,1200,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(14,1300,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(15,1400,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(16,1500,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(17,1600,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(18,1700,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(19,1800,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24'),
(20,2000,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,NULL,'2025-04-17 08:25:24');
/*!40000 ALTER TABLE `levels` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `npc_vendor_items`
--

DROP TABLE IF EXISTS `npc_vendor_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `npc_vendor_items` (
  `vendor_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `price` int(11) DEFAULT 0,
  `stock` int(11) DEFAULT NULL,
  `instance_stock` int(11) DEFAULT NULL,
  PRIMARY KEY (`vendor_id`,`item_id`),
  KEY `item_id` (`item_id`),
  CONSTRAINT `npc_vendor_items_ibfk_1` FOREIGN KEY (`vendor_id`) REFERENCES `npc_vendors` (`vendor_id`) ON DELETE CASCADE,
  CONSTRAINT `npc_vendor_items_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `npc_vendor_items`
--

LOCK TABLES `npc_vendor_items` WRITE;
/*!40000 ALTER TABLE `npc_vendor_items` DISABLE KEYS */;
INSERT INTO `npc_vendor_items` VALUES
(1,1,50,3,2),
(1,3,100,3,1),
(1,4,500,3,3),
(2,4,500,3,3),
(2,5,500,10,10),
(2,9,150,3,3);
/*!40000 ALTER TABLE `npc_vendor_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `npc_vendors`
--

DROP TABLE IF EXISTS `npc_vendors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `npc_vendors` (
  `vendor_id` int(11) NOT NULL AUTO_INCREMENT,
  `vendor_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `inventory` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`inventory`)),
  `image_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`vendor_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `npc_vendors`
--

LOCK TABLES `npc_vendors` WRITE;
/*!40000 ALTER TABLE `npc_vendors` DISABLE KEYS */;
INSERT INTO `npc_vendors` VALUES
(1,'Stiltzkin','__**Stiltzkin:**__\n\n**\"Oh hello, I’m glad to see you are not a monster, kupo! I’m a traveling merchant, see.. I was portal hopping and suddenly came across a black portal I’d never seen before...\"**\n\nStiltzkin looks at you as if he’s trying to recall something. **\"Have we met before, kupo? You seem familiar.\"**\n\n**\"At any rate, if you’d like to buy or sell something the shop is still open.\"**',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1362946279587713074/stiltzkin.gif?ex=68345ce3&is=68330b63&hm=b99988391998062f540188581a94327b15919d6d620bf7fe8dae6a953e29ba24&','2025-03-24 22:37:28'),
(2,'Artemecion','__**Artemecion:**__\n\n\"Hey you aren\'t a monster, Kupo! Do you need a **Letter** delivered by chance? \n\nNo? Hmph, well I also sell a few wares I find along my journey, kupo.\"\n\n*Artemecion pauses for a moment, it looks as though he\'s trying to recall something...*\n\n\"Sorry... your face reminds me of **someone I haven\'t seen in a long time**, kupo. I was lost in a good memory for a moment. \n\nFeel free to browse, but my dyes are off limits, kupo!\"',NULL,'https://cdn.discordapp.com/attachments/1362832151485354065/1376308818199445604/Artemecion.gif?ex=6834daf8&is=68338978&hm=16ecf8b4fff715e695e67f6c647a7dc918bf8cfb0486ac383cb337e22f380efd&','2025-05-26 02:31:53');
/*!40000 ALTER TABLE `npc_vendors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `player_eidolons`
--

DROP TABLE IF EXISTS `player_eidolons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_eidolons` (
  `session_id` int(11) NOT NULL,
  `player_id` bigint(20) NOT NULL,
  `eidolon_id` int(11) NOT NULL,
  `level` int(11) DEFAULT 1,
  `experience` int(11) DEFAULT 0,
  `unlocked_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`session_id`,`player_id`,`eidolon_id`),
  KEY `player_id` (`player_id`,`session_id`),
  KEY `eidolon_id` (`eidolon_id`),
  CONSTRAINT `player_eidolons_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE,
  CONSTRAINT `player_eidolons_ibfk_2` FOREIGN KEY (`player_id`, `session_id`) REFERENCES `players` (`player_id`, `session_id`) ON DELETE CASCADE,
  CONSTRAINT `player_eidolons_ibfk_3` FOREIGN KEY (`eidolon_id`) REFERENCES `eidolons` (`eidolon_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `player_eidolons`
--

LOCK TABLES `player_eidolons` WRITE;
/*!40000 ALTER TABLE `player_eidolons` DISABLE KEYS */;
/*!40000 ALTER TABLE `player_eidolons` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `player_temporary_abilities`
--

DROP TABLE IF EXISTS `player_temporary_abilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_temporary_abilities` (
  `session_id` int(11) NOT NULL,
  `player_id` bigint(20) NOT NULL,
  `temp_ability_id` int(11) NOT NULL,
  `remaining_turns` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`session_id`,`player_id`,`temp_ability_id`),
  KEY `temp_ability_id` (`temp_ability_id`),
  KEY `player_id` (`player_id`,`session_id`),
  CONSTRAINT `player_temporary_abilities_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE,
  CONSTRAINT `player_temporary_abilities_ibfk_2` FOREIGN KEY (`temp_ability_id`) REFERENCES `temporary_abilities` (`temp_ability_id`) ON DELETE CASCADE,
  CONSTRAINT `player_temporary_abilities_ibfk_3` FOREIGN KEY (`player_id`, `session_id`) REFERENCES `players` (`player_id`, `session_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `player_temporary_abilities`
--

LOCK TABLES `player_temporary_abilities` WRITE;
/*!40000 ALTER TABLE `player_temporary_abilities` DISABLE KEYS */;
/*!40000 ALTER TABLE `player_temporary_abilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `players`
--

DROP TABLE IF EXISTS `players`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `players` (
  `player_id` bigint(20) NOT NULL,
  `session_id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `class_id` int(11) DEFAULT NULL,
  `level` int(11) DEFAULT 1,
  `experience` int(11) DEFAULT 0,
  `hp` int(11) DEFAULT 100,
  `max_hp` int(11) DEFAULT 100,
  `mp` int(11) DEFAULT 0,
  `max_mp` int(11) DEFAULT 0,
  `attack_power` int(11) DEFAULT 10,
  `defense` int(11) DEFAULT 5,
  `magic_power` int(11) DEFAULT 10,
  `magic_defense` int(11) DEFAULT 5,
  `accuracy` int(11) DEFAULT 95,
  `evasion` int(11) DEFAULT 5,
  `speed` int(11) DEFAULT 10,
  `coord_x` int(11) DEFAULT 0,
  `coord_y` int(11) DEFAULT 0,
  `current_floor_id` int(11) DEFAULT NULL,
  `inventory` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`inventory`)),
  `discovered_rooms` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`discovered_rooms`)),
  `gil` int(11) DEFAULT 0,
  `status_effects` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`status_effects`)),
  `is_dead` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `kill_count` int(11) NOT NULL DEFAULT 0,
  `enemies_defeated` int(11) DEFAULT 0,
  `rooms_visited` int(11) DEFAULT 0,
  `gil_earned` int(11) DEFAULT 0,
  `bosses_defeated` int(11) DEFAULT 0,
  `current_floor` int(11) DEFAULT 1,
  PRIMARY KEY (`player_id`,`session_id`),
  KEY `session_id` (`session_id`),
  KEY `class_id` (`class_id`),
  CONSTRAINT `players_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE,
  CONSTRAINT `players_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`class_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `players`
--

LOCK TABLES `players` WRITE;
/*!40000 ALTER TABLE `players` DISABLE KEYS */;
INSERT INTO `players` VALUES
(821995310179155999,1,'Blink',12,1,0,480,480,160,160,15,5,20,1,99,1,10,0,0,1,'{}','[]',0,'[]',0,'2025-12-21 00:14:14','2025-12-21 00:14:46',0,0,0,0,0,1),
(821995310179155999,2,'Blink',12,1,80,411,480,160,160,15,5,20,1,99,1,10,9,4,1,'{\"1\": 2, \"4\": 1}','[[1, 7, 4], [1, 2, 5], [1, 4, 5], [1, 9, 4], [1, 8, 2], [1, 0, 1], [1, 9, 1], [1, 0, 4], [1, 1, 3], [1, 0, 7], [1, 1, 6], [1, 6, 5], [1, 7, 3], [1, 2, 4], [1, 3, 5], [1, 8, 1], [1, 1, 2], [1, 0, 0], [1, 0, 6], [1, 9, 3], [1, 5, 5], [1, 7, 5], [1, 2, 6], [1, 2, 3], [1, 8, 3], [1, 9, 2], [1, 1, 4], [1, 0, 2], [1, 1, 7], [1, 0, 5]]',430,'[]',0,'2025-12-21 01:12:56','2025-12-21 01:51:09',0,0,0,0,0,1);
/*!40000 ALTER TABLE `players` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `room_templates`
--

DROP TABLE IF EXISTS `room_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `room_templates` (
  `template_id` int(11) NOT NULL AUTO_INCREMENT,
  `room_type` enum('safe','entrance','monster','item','shop','boss','trap','illusion','staircase_up','staircase_down','exit','locked','chest_unlocked','miniboss','death','cloister') NOT NULL DEFAULT 'safe',
  `template_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `default_enemy_id` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `trap_type` enum('spike','gil_snatcher','mimic') DEFAULT NULL,
  `trap_payload` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`trap_payload`)),
  `eidolon_id` int(11) DEFAULT NULL,
  `attune_level` int(11) DEFAULT NULL,
  PRIMARY KEY (`template_id`),
  KEY `default_enemy_id` (`default_enemy_id`),
  KEY `eidolon_id` (`eidolon_id`),
  CONSTRAINT `room_templates_ibfk_1` FOREIGN KEY (`default_enemy_id`) REFERENCES `enemies` (`enemy_id`) ON DELETE SET NULL,
  CONSTRAINT `room_templates_ibfk_2` FOREIGN KEY (`eidolon_id`) REFERENCES `eidolons` (`eidolon_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `room_templates`
--

LOCK TABLES `room_templates` WRITE;
/*!40000 ALTER TABLE `room_templates` DISABLE KEYS */;
INSERT INTO `room_templates` VALUES
(1,'safe','Moss Room','You do not notice anything of importance, the area appears to be safe.','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'2025-03-31 12:40:47',NULL,NULL,NULL,NULL),
(2,'safe','Mystic Room','You do not notice anything of importance, the area appears to be safe.','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'2025-03-31 12:40:47',NULL,NULL,NULL,NULL),
(3,'safe','Crystal Tunnel','You do not notice anything of importance, the area appears to be safe.','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'2025-03-31 12:40:47',NULL,NULL,NULL,NULL),
(4,'safe','Bridge','You do not notice anything of importance, the area appears to be safe.','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'2025-04-10 06:22:14',NULL,NULL,NULL,NULL),
(5,'safe','Magicite','You do not notice anything of importance, the area appears to be safe.','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'2025-04-10 06:22:19',NULL,NULL,NULL,NULL),
(6,'safe','Rainbow Crystal','You do not notice anything of importance, the area appears to be safe.','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'2025-04-10 06:22:27',NULL,NULL,NULL,NULL),
(7,'safe','Aetheryte','You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'2025-04-10 06:22:27',NULL,NULL,NULL,NULL),
(8,'monster','You Sense A Hostile Presence...','An enemy appears upon entering the area...','',NULL,'2025-03-31 12:40:47',NULL,NULL,NULL,NULL),
(9,'staircase_up','Staircase Up','You notice a staircase leading up to the next level.','https://cdn.discordapp.com/attachments/1362832151485354065/1362832388677308516/stairs.png?ex=680c65d1&is=680b1451&hm=8b5d73c9b00898e7913c5d661d2f107731817084c19a8f938f7ce9ec3637340d&',NULL,'2025-04-19 23:55:00',NULL,NULL,NULL,NULL),
(10,'staircase_down','Staircase Down','You notice a staircase leading down to the next level.','https://cdn.discordapp.com/attachments/1362832151485354065/1365404303161950388/stairs_down_2.png?ex=680d2f59&is=680bddd9&hm=94fbe622374098bfcb2d17d0ffaaadeca5cfafa526db4273c28c02faf&',NULL,'2025-04-19 23:55:00',NULL,NULL,NULL,NULL),
(11,'exit','Dungeon Exit','(Implemented in next patch)','https://the-demiurge.com/DemiDevUnit/images/backintro.png',NULL,'2025-03-31 07:40:47',NULL,NULL,NULL,NULL),
(12,'item','Treasure Room','You do not notice any hostile presence,\ninstead you see a treasure chest waiting to be unlocked.','https://cdn.discordapp.com/attachments/1362832151485354065/1362832389629284544/treasurechest.png?ex=680c65d1&is=680b1451&hm=e1971818f32f4e0b0f43cfcbf5283fc1c3f36f80b1af2bcfacbfd7ba8ecf3ace&',NULL,'2025-03-31 07:40:47',NULL,NULL,NULL,NULL),
(13,'boss','Boss Lair','A grand chamber with ominous decorations.',NULL,17,'2025-03-31 07:40:47',NULL,NULL,NULL,NULL),
(15,'shop','Shop Room','You do not notice any hostile presence.\n\nInstead you find a Moogle hiding in the corner...','https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&',NULL,'2025-03-31 07:40:47',NULL,NULL,NULL,NULL),
(16,'illusion','Illusion Chamber','The room shimmers mysteriously...','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385040711930/Illusion.png?ex=680c65d0&is=680b1450&hm=17f9b558f22f2738b576bb373eec18b161c8df67c8f2bcfff86a1ddc6d604eed&',NULL,'2025-03-31 07:40:47',NULL,NULL,NULL,NULL),
(17,'locked','Locked Door','A heavy door with a glowing symbol and what appears to be a lock. It seems you need a key.','https://cdn.discordapp.com/attachments/1362832151485354065/1362832387742109886/lockedroom.png?ex=680d0e91&is=680bbd11&hm=d3b19049954366cd7d625e5592a6cffbf7242aa3462ea107525c4919c371bee3&',NULL,'2025-04-19 23:55:00',NULL,NULL,NULL,NULL),
(18,'chest_unlocked','Unlocked Chest','You notice an empty chest and nothing else of importance.','https://cdn.discordapp.com/attachments/1362832151485354065/1365404301488291880/chestopen.png?ex=680d2f59&is=680bddd9&hm=df9e2742340f802058c078a816d17d0ffaaadeca5cfafa526db4273c28c02faf&',NULL,'2025-04-24 04:00:00',NULL,NULL,NULL,NULL),
(19,'safe','Lake Room','You do not notice anything of importance, the area appears to be safe.','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'2025-04-25 17:29:10',NULL,NULL,NULL,NULL),
(20,'safe','Lake Room 2','You do not notice anything of importance, the area appears to be safe.','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'2025-04-25 17:29:10',NULL,NULL,NULL,NULL),
(21,'miniboss','Mimic','As you approach the locked chest it springs to life and bares it\'s fangs!','https://cdn.discordapp.com/attachments/1362832151485354065/1365786181417177148/2.png?ex=68113600&is=680fe480&hm=a35ce81d097c19b34c06338bb678627ec9b16061ba867cb0d72be0d84075a927&',16,'2025-04-29 05:24:47',NULL,NULL,NULL,NULL),
(22,'death','Death','Your health as fallen to 0 and have fainted.','https://cdn.discordapp.com/attachments/1362832151485354065/1370837025665712178/output.gif?ex=6820f2f7&is=681fa177&hm=5c0ff142cc94ff7dd4050fb0be0cb1821580e251f6c5e8cb2f31384170afbd52&',NULL,'2025-05-09 21:59:31',NULL,NULL,NULL,NULL),
(23,'entrance','Dungeon Entrance','You arrive at the dungeon entrance. The air is calm, and the path ahead beckons you forward.','https://cdn.discordapp.com/attachments/1362832151485354065/1451193431446655107/entrance.png?ex=6947ebb3&is=69469a33&hm=83309aec93d17392e9025d9e1927254b7bddb594fe3a7d24168e4dc0963638a3&',NULL,'2025-06-23 17:00:00',NULL,NULL,NULL,NULL),
(24,'cloister','Cloister of Flames','You sense a great power in this cloister. A crimson Aetheryte crystal hums softly at its center.','https://cdn.discordapp.com/attachments/1362832151485354065/1451958079330713773/5ff3c362-8b62-4b7c-9202-ceb4bf75ade3.png?ex=694810d6&is=6946bf56&hm=96ccb56188e13de07f19215e22fc2e79168cbe67cbd28350b13476498587102e&',NULL,'2025-07-01 05:00:00',NULL,NULL,1,5),
(25,'cloister','Cloister of Frost','You sense a great power in this cloister. A pale Aetheryte crystal floats, cold mist curling from it.','https://cdn.discordapp.com/attachments/1362832151485354065/1451958423640998113/c49919eb-242f-44d3-a266-225a6e5c679c.png?ex=69481128&is=6946bfa8&hm=7dc2e3d176f318651b25292cf9a74fad0aca9f957de9a794876fe746cac999ee&',NULL,'2025-07-01 05:00:00',NULL,NULL,2,8),
(26,'cloister','Cloister of Storms','You sense a great power in this cloister. A crackling Aetheryte crystal pulses with thunder.','https://cdn.discordapp.com/attachments/1362832151485354065/1451958653082009771/14d77bc2-a1ab-49e7-bdf8-f02a5d9a3d7e.png?ex=6948115e&is=6946bfde&hm=c125b318a8b92f9dfc4faf6331c67f609b1a6c231e4044c73421dcfe3a9573c7&',NULL,'2025-07-01 05:00:00',NULL,NULL,3,12);
/*!40000 ALTER TABLE `room_templates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rooms`
--

DROP TABLE IF EXISTS `rooms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `rooms` (
  `room_id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` int(11) NOT NULL,
  `floor_id` int(11) NOT NULL,
  `coord_x` int(11) NOT NULL,
  `coord_y` int(11) NOT NULL,
  `description` text DEFAULT NULL,
  `room_type` varchar(64) NOT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `default_enemy_id` int(11) DEFAULT NULL,
  `exits` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`exits`)),
  `has_encounter` tinyint(1) DEFAULT 0,
  `vendor_id` int(11) DEFAULT NULL,
  `stair_up_floor_id` int(11) DEFAULT NULL,
  `stair_up_x` int(11) DEFAULT NULL,
  `stair_up_y` int(11) DEFAULT NULL,
  `stair_down_floor_id` int(11) DEFAULT NULL,
  `stair_down_x` int(11) DEFAULT NULL,
  `stair_down_y` int(11) DEFAULT NULL,
  `inner_template_id` int(11) DEFAULT NULL,
  `eidolon_id` int(11) DEFAULT NULL,
  `attune_level` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `stair_up_floor` int(11) DEFAULT NULL,
  `stair_down_floor` int(11) DEFAULT NULL,
  PRIMARY KEY (`room_id`),
  KEY `session_id` (`session_id`),
  KEY `floor_id` (`floor_id`),
  KEY `vendor_id` (`vendor_id`),
  KEY `inner_template_id` (`inner_template_id`),
  KEY `eidolon_id` (`eidolon_id`),
  CONSTRAINT `rooms_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE,
  CONSTRAINT `rooms_ibfk_2` FOREIGN KEY (`floor_id`) REFERENCES `floors` (`floor_id`) ON DELETE CASCADE,
  CONSTRAINT `rooms_ibfk_3` FOREIGN KEY (`vendor_id`) REFERENCES `session_vendor_instances` (`session_vendor_id`) ON DELETE SET NULL,
  CONSTRAINT `rooms_ibfk_4` FOREIGN KEY (`inner_template_id`) REFERENCES `room_templates` (`template_id`) ON DELETE SET NULL,
  CONSTRAINT `rooms_ibfk_5` FOREIGN KEY (`eidolon_id`) REFERENCES `eidolons` (`eidolon_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=207 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rooms`
--

LOCK TABLES `rooms` WRITE;
/*!40000 ALTER TABLE `rooms` DISABLE KEYS */;
INSERT INTO `rooms` VALUES
(1,2,1,0,0,'You arrive at the dungeon entrance. The air is calm, and the path ahead beckons you forward.','entrance','https://cdn.discordapp.com/attachments/1362832151485354065/1451193431446655107/entrance.png?ex=6947ebb3&is=69469a33&hm=83309aec93d17392e9025d9e1927254b7bddb594fe3a7d24168e4dc0963638a3&',NULL,'{\"south\": [0, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(2,2,1,1,0,'You sense a great power in this cloister. A crimson Aetheryte crystal hums softly at its center.','cloister','https://cdn.discordapp.com/attachments/1362832151485354065/1451958079330713773/5ff3c362-8b62-4b7c-9202-ceb4bf75ade3.png?ex=694810d6&is=6946bf56&hm=96ccb56188e13de07f19215e22fc2e79168cbe67cbd28350b13476498587102e&',NULL,'{\"south\": [1, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,5,'2025-12-21 01:14:04',NULL,NULL),
(3,2,1,2,0,'You sense a great power in this cloister. A crackling Aetheryte crystal pulses with thunder.','cloister','https://cdn.discordapp.com/attachments/1362832151485354065/1451958653082009771/14d77bc2-a1ab-49e7-bdf8-f02a5d9a3d7e.png?ex=6948115e&is=6946bfde&hm=c125b318a8b92f9dfc4faf6331c67f609b1a6c231e4044c73421dcfe3a9573c7&',NULL,'{\"south\": [2, 1], \"east\": [3, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,3,12,'2025-12-21 01:14:04',NULL,NULL),
(4,2,1,3,0,'You sense a great power in this cloister. A pale Aetheryte crystal floats, cold mist curling from it.','cloister','https://cdn.discordapp.com/attachments/1362832151485354065/1451958423640998113/c49919eb-242f-44d3-a266-225a6e5c679c.png?ex=69481128&is=6946bfa8&hm=7dc2e3d176f318651b25292cf9a74fad0aca9f957de9a794876fe746cac999ee&',NULL,'{\"south\": [3, 1], \"west\": [2, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,2,8,'2025-12-21 01:14:04',NULL,NULL),
(5,2,1,4,0,'An enemy appears upon entering the area...','monster','',21,'{\"south\": [4, 1], \"east\": [5, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(6,2,1,5,0,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"east\": [6, 0], \"west\": [4, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(7,2,1,6,0,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"east\": [7, 0], \"west\": [5, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(8,2,1,7,0,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"east\": [8, 0], \"west\": [6, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(9,2,1,8,0,'You do not notice any hostile presence.\n\nInstead you find a Moogle hiding in the corner...','shop','https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&',NULL,'{\"east\": [9, 0], \"west\": [7, 0]}',0,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(10,2,1,9,0,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"south\": [9, 1], \"west\": [8, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(12,2,1,1,1,'An enemy appears upon entering the area...','monster','',22,'{\"north\": [1, 0], \"east\": [2, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(13,2,1,2,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"north\": [2, 0], \"south\": [2, 2], \"east\": [3, 1], \"west\": [1, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(14,2,1,3,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"north\": [3, 0], \"south\": [3, 2], \"west\": [2, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(15,2,1,4,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"north\": [4, 0], \"east\": [5, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(16,2,1,5,1,'The room shimmers mysteriously...','illusion','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385040711930/Illusion.png?ex=680c65d0&is=680b1450&hm=17f9b558f22f2738b576bb373eec18b161c8df67c8f2bcfff86a1ddc6d604eed&',NULL,'{\"east\": [6, 1], \"west\": [4, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(17,2,1,6,1,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"east\": [7, 1], \"west\": [5, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(18,2,1,7,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"south\": [7, 2], \"west\": [6, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(19,2,1,8,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"south\": [8, 2], \"east\": [9, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(20,2,1,9,1,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"north\": [9, 0], \"south\": [9, 2], \"west\": [8, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(21,2,1,0,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"north\": [0, 1], \"east\": [1, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(22,2,1,1,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"south\": [1, 3], \"west\": [0, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(23,2,1,2,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [2, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(24,2,1,3,2,'An enemy appears upon entering the area...','monster','',19,'{\"north\": [3, 1], \"south\": [3, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(25,2,1,4,2,'An enemy appears upon entering the area...','monster','',8,'{\"south\": [4, 3], \"east\": [5, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(26,2,1,5,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"east\": [6, 2], \"west\": [4, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(27,2,1,6,2,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"east\": [7, 2], \"west\": [5, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(28,2,1,7,2,'An enemy appears upon entering the area...','monster','',4,'{\"north\": [7, 1], \"west\": [6, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(29,2,1,8,2,'You do not notice any hostile presence.\n\nInstead you find a Moogle hiding in the corner...','shop','https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&',NULL,'{\"north\": [8, 1], \"south\": [8, 3]}',0,2,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(30,2,1,9,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'{\"north\": [9, 1], \"south\": [9, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(31,2,1,0,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"south\": [0, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(32,2,1,1,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"north\": [1, 2], \"east\": [2, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(33,2,1,2,3,'You do not notice any hostile presence.\n\nInstead you find a Moogle hiding in the corner...','shop','https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&',NULL,'{\"south\": [2, 4], \"west\": [1, 3]}',0,3,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(34,2,1,3,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"north\": [3, 2], \"south\": [3, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(35,2,1,4,3,'An enemy appears upon entering the area...','monster','',21,'{\"north\": [4, 2], \"east\": [5, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(36,2,1,5,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"east\": [6, 3], \"west\": [4, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(37,2,1,6,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"south\": [6, 4], \"west\": [5, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(38,2,1,7,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"south\": [7, 4], \"east\": [8, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(39,2,1,8,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"north\": [8, 2], \"west\": [7, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(41,2,1,0,4,'You do not notice any hostile presence.\n\nInstead you find a Moogle hiding in the corner...','shop','https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&',NULL,'{\"north\": [0, 3], \"south\": [0, 5], \"east\": [1, 4]}',0,4,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(42,2,1,1,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"east\": [2, 4], \"west\": [0, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(43,2,1,2,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"north\": [2, 3], \"west\": [1, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(44,2,1,3,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"north\": [3, 3], \"east\": [4, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(45,2,1,4,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"east\": [5, 4], \"west\": [3, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(46,2,1,5,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"east\": [6, 4], \"west\": [4, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(47,2,1,6,4,'An enemy appears upon entering the area...','monster','',13,'{\"north\": [6, 3], \"west\": [5, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(49,2,1,8,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"south\": [8, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(50,2,1,9,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"north\": [9, 3], \"south\": [9, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(52,2,1,1,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"east\": [2, 5], \"west\": [0, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(53,2,1,2,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"south\": [2, 6], \"east\": [3, 5], \"west\": [1, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(54,2,1,3,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'{\"east\": [4, 5], \"west\": [2, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(55,2,1,4,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"east\": [5, 5], \"west\": [3, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(57,2,1,6,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"east\": [7, 5], \"west\": [5, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(58,2,1,7,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"north\": [7, 4], \"west\": [6, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(59,2,1,8,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"north\": [8, 4], \"south\": [8, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(60,2,1,9,5,'An enemy appears upon entering the area...','monster','',20,'{\"north\": [9, 4], \"south\": [9, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(61,2,1,0,6,'A heavy door with a glowing symbol and what appears to be a lock. It seems you need a key.','locked','https://cdn.discordapp.com/attachments/1362832151485354065/1362832387742109886/lockedroom.png?ex=680d0e91&is=680bbd11&hm=d3b19049954366cd7d625e5592a6cffbf7242aa3462ea107525c4919c371bee3&',16,'{\"north\": [0, 5], \"south\": [0, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,21,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(62,2,1,1,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"south\": [1, 7], \"east\": [2, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(63,2,1,2,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"north\": [2, 5], \"west\": [1, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(64,2,1,3,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'{\"east\": [4, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(65,2,1,4,6,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"south\": [4, 7], \"east\": [5, 6], \"west\": [3, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(66,2,1,5,6,'An enemy appears upon entering the area...','monster','',19,'{\"south\": [5, 7], \"west\": [4, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(67,2,1,6,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'{\"south\": [6, 7], \"east\": [7, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(68,2,1,7,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"south\": [7, 7], \"east\": [8, 6], \"west\": [6, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(69,2,1,8,6,'An enemy appears upon entering the area...','monster','',5,'{\"north\": [8, 5], \"west\": [7, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(70,2,1,9,6,'An enemy appears upon entering the area...','monster','',10,'{\"north\": [9, 5], \"south\": [9, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(71,2,1,0,7,'You do not notice any hostile presence,\ninstead you see a treasure chest waiting to be unlocked.','staircase_up','https://cdn.discordapp.com/attachments/1362832151485354065/1362832389629284544/treasurechest.png?ex=680c65d1&is=680b1451&hm=e1971818f32f4e0b0f43cfcbf5283fc1c3f36f80b1af2bcfacbfd7ba8ecf3ace&',NULL,'{\"north\": [0, 6], \"east\": [1, 7]}',0,NULL,2,0,7,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(73,2,1,2,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"south\": [2, 8], \"east\": [3, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(74,2,1,3,7,'An enemy appears upon entering the area...','monster','',3,'{\"south\": [3, 8], \"east\": [4, 7], \"west\": [2, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(75,2,1,4,7,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"north\": [4, 6], \"west\": [3, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(76,2,1,5,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"north\": [5, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(77,2,1,6,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"north\": [6, 6], \"south\": [6, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(78,2,1,7,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"north\": [7, 6], \"east\": [8, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(79,2,1,8,7,'The room shimmers mysteriously...','illusion','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385040711930/Illusion.png?ex=680c65d0&is=680b1450&hm=17f9b558f22f2738b576bb373eec18b161c8df67c8f2bcfff86a1ddc6d604eed&',NULL,'{\"east\": [9, 7], \"west\": [7, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(80,2,1,9,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"north\": [9, 6], \"south\": [9, 8], \"west\": [8, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(81,2,1,0,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"south\": [0, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(82,2,1,1,8,'The room shimmers mysteriously...','illusion','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385040711930/Illusion.png?ex=680c65d0&is=680b1450&hm=17f9b558f22f2738b576bb373eec18b161c8df67c8f2bcfff86a1ddc6d604eed&',NULL,'{\"south\": [1, 9], \"east\": [2, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(83,2,1,2,8,'An enemy appears upon entering the area...','monster','',25,'{\"north\": [2, 7], \"south\": [2, 9], \"west\": [1, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(84,2,1,3,8,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"north\": [3, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(85,2,1,4,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"south\": [4, 9], \"east\": [5, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(86,2,1,5,8,'An enemy appears upon entering the area...','monster','',7,'{\"east\": [6, 8], \"west\": [4, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(87,2,1,6,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'{\"north\": [6, 7], \"west\": [5, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(88,2,1,7,8,'An enemy appears upon entering the area...','monster','',21,'{\"east\": [8, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(89,2,1,8,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"east\": [9, 8], \"west\": [7, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(90,2,1,9,8,'An enemy appears upon entering the area...','monster','',13,'{\"north\": [9, 7], \"south\": [9, 9], \"west\": [8, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(91,2,1,0,9,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"north\": [0, 8], \"east\": [1, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(92,2,1,1,9,'An enemy appears upon entering the area...','monster','',15,'{\"north\": [1, 8], \"west\": [0, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(93,2,1,2,9,'An enemy appears upon entering the area...','monster','',3,'{\"north\": [2, 8], \"east\": [3, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(94,2,1,3,9,'An enemy appears upon entering the area...','monster','',25,'{\"east\": [4, 9], \"west\": [2, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(95,2,1,4,9,'An enemy appears upon entering the area...','monster','',11,'{\"north\": [4, 8], \"east\": [5, 9], \"west\": [3, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(96,2,1,5,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"east\": [6, 9], \"west\": [4, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(97,2,1,6,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"east\": [7, 9], \"west\": [5, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(98,2,1,7,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"east\": [8, 9], \"west\": [6, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(99,2,1,8,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"east\": [9, 9], \"west\": [7, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(100,2,1,9,9,'An enemy appears upon entering the area...','monster','',18,'{\"north\": [9, 8], \"west\": [8, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(101,2,2,0,0,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"east\": [1, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(102,2,2,1,0,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"south\": [1, 1], \"west\": [0, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(103,2,2,2,0,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"south\": [2, 1], \"east\": [3, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(104,2,2,3,0,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"south\": [3, 1], \"west\": [2, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(105,2,2,4,0,'An enemy appears upon entering the area...','monster','',19,'{\"south\": [4, 1], \"east\": [5, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(106,2,2,5,0,'A grand chamber with ominous decorations.','boss',NULL,17,'{\"east\": [6, 0], \"west\": [4, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(107,2,2,6,0,'The room shimmers mysteriously...','illusion','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385040711930/Illusion.png?ex=680c65d0&is=680b1450&hm=17f9b558f22f2738b576bb373eec18b161c8df67c8f2bcfff86a1ddc6d604eed&',NULL,'{\"east\": [7, 0], \"west\": [5, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(108,2,2,7,0,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'{\"south\": [7, 1], \"west\": [6, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(109,2,2,8,0,'An enemy appears upon entering the area...','monster','',2,'{\"south\": [8, 1], \"east\": [9, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(110,2,2,9,0,'An enemy appears upon entering the area...','monster','',5,'{\"west\": [8, 0]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(111,2,2,0,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"south\": [0, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(112,2,2,1,1,'You do not notice any hostile presence.\n\nInstead you find a Moogle hiding in the corner...','shop','https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&',NULL,'{\"north\": [1, 0], \"south\": [1, 2]}',0,5,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(113,2,2,2,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"north\": [2, 0], \"south\": [2, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(114,2,2,3,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"north\": [3, 0], \"east\": [4, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(115,2,2,4,1,'You do not notice any hostile presence.\n\nInstead you find a Moogle hiding in the corner...','shop','https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&',NULL,'{\"north\": [4, 0], \"west\": [3, 1]}',0,6,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(116,2,2,5,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"south\": [5, 2], \"east\": [6, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(117,2,2,6,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"east\": [7, 1], \"west\": [5, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(118,2,2,7,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"north\": [7, 0], \"west\": [6, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(119,2,2,8,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"north\": [8, 0], \"east\": [9, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(120,2,2,9,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"south\": [9, 2], \"west\": [8, 1]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(121,2,2,0,2,'An enemy appears upon entering the area...','monster','',7,'{\"north\": [0, 1], \"south\": [0, 3], \"east\": [1, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(122,2,2,1,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"north\": [1, 1], \"west\": [0, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(123,2,2,2,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [2, 1], \"south\": [2, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(124,2,2,3,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"east\": [4, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(125,2,2,4,2,'An enemy appears upon entering the area...','monster','',21,'{\"east\": [5, 2], \"west\": [3, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(126,2,2,5,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [5, 1], \"east\": [6, 2], \"west\": [4, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(127,2,2,6,2,'An enemy appears upon entering the area...','monster','',2,'{\"east\": [7, 2], \"west\": [5, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(128,2,2,7,2,'An enemy appears upon entering the area...','monster','',5,'{\"east\": [8, 2], \"west\": [6, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(129,2,2,8,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"east\": [9, 2], \"west\": [7, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(130,2,2,9,2,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [9, 1], \"south\": [9, 3], \"west\": [8, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(131,2,2,0,3,'An enemy appears upon entering the area...','monster','',12,'{\"north\": [0, 2], \"south\": [0, 4], \"east\": [1, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(132,2,2,1,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"south\": [1, 4], \"east\": [2, 3], \"west\": [0, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(133,2,2,2,3,'An enemy appears upon entering the area...','monster','',7,'{\"north\": [2, 2], \"east\": [3, 3], \"west\": [1, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(134,2,2,3,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"east\": [4, 3], \"west\": [2, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(135,2,2,4,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'{\"south\": [4, 4], \"west\": [3, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(136,2,2,5,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"south\": [5, 4], \"east\": [6, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(137,2,2,6,3,'A grand chamber with ominous decorations.','boss',NULL,17,'{\"east\": [7, 3], \"west\": [5, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(138,2,2,7,3,'(Implemented in next patch)','exit','https://the-demiurge.com/DemiDevUnit/images/backintro.png',NULL,'{\"south\": [7, 4], \"east\": [8, 3], \"west\": [6, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(139,2,2,8,3,'An enemy appears upon entering the area...','monster','',5,'{\"south\": [8, 4], \"west\": [7, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(140,2,2,9,3,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"north\": [9, 2], \"south\": [9, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(141,2,2,0,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"north\": [0, 3], \"south\": [0, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(142,2,2,1,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"north\": [1, 3], \"south\": [1, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(143,2,2,2,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"south\": [2, 5], \"east\": [3, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(144,2,2,3,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"south\": [3, 5], \"west\": [2, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(145,2,2,4,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"north\": [4, 3], \"south\": [4, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(146,2,2,5,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"north\": [5, 3], \"south\": [5, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(147,2,2,6,4,'An enemy appears upon entering the area...','monster','',20,'{\"south\": [6, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(148,2,2,7,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [7, 3], \"south\": [7, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(149,2,2,8,4,'You sense a great power in this cloister. A crackling Aetheryte crystal pulses with thunder.','cloister','https://cdn.discordapp.com/attachments/1362832151485354065/1451958653082009771/14d77bc2-a1ab-49e7-bdf8-f02a5d9a3d7e.png?ex=6948115e&is=6946bfde&hm=c125b318a8b92f9dfc4faf6331c67f609b1a6c231e4044c73421dcfe3a9573c7&',NULL,'{\"north\": [8, 3]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,3,12,'2025-12-21 01:14:04',NULL,NULL),
(150,2,2,9,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"north\": [9, 3], \"south\": [9, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(151,2,2,0,5,'An enemy appears upon entering the area...','monster','',11,'{\"north\": [0, 4], \"south\": [0, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(152,2,2,1,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"north\": [1, 4], \"east\": [2, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(153,2,2,2,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"north\": [2, 4], \"south\": [2, 6], \"west\": [1, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(154,2,2,3,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"north\": [3, 4], \"south\": [3, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(155,2,2,4,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'{\"north\": [4, 4], \"south\": [4, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(156,2,2,5,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [5, 4], \"south\": [5, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(157,2,2,6,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"north\": [6, 4], \"south\": [6, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(158,2,2,7,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"north\": [7, 4], \"east\": [8, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(159,2,2,8,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'{\"south\": [8, 6], \"west\": [7, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(160,2,2,9,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"north\": [9, 4], \"south\": [9, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(161,2,2,0,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"north\": [0, 5], \"south\": [0, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(162,2,2,1,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"south\": [1, 7], \"east\": [2, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(163,2,2,2,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [2, 5], \"west\": [1, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(164,2,2,3,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"north\": [3, 5], \"south\": [3, 7], \"east\": [4, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(165,2,2,4,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"north\": [4, 5], \"west\": [3, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(166,2,2,5,6,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"north\": [5, 5], \"south\": [5, 7], \"east\": [6, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(167,2,2,6,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&',NULL,'{\"north\": [6, 5], \"south\": [6, 7], \"west\": [5, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(168,2,2,7,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"south\": [7, 7], \"east\": [8, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(169,2,2,8,6,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"north\": [8, 5], \"west\": [7, 6]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(170,2,2,9,6,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"north\": [9, 5], \"south\": [9, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(171,2,2,0,7,'You notice a staircase leading down to the next level.','staircase_down','https://cdn.discordapp.com/attachments/1362832151485354065/1365404303161950388/stairs_down_2.png?ex=680d2f59&is=680bddd9&hm=94fbe622374098bfcb2d17d0ffaaadeca5cfafa526db4273c28c02faf&',NULL,'{\"north\": [0, 6], \"east\": [1, 7]}',0,NULL,NULL,NULL,NULL,1,0,7,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(172,2,2,1,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"north\": [1, 6], \"east\": [2, 7], \"west\": [0, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(173,2,2,2,7,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"south\": [2, 8], \"east\": [3, 7], \"west\": [1, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(174,2,2,3,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"north\": [3, 6], \"south\": [3, 8], \"east\": [4, 7], \"west\": [2, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(175,2,2,4,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"west\": [3, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(176,2,2,5,7,'You do not notice any hostile presence.\n\nInstead you find a Moogle hiding in the corner...','shop','https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&',NULL,'{\"north\": [5, 6], \"south\": [5, 8], \"east\": [6, 7]}',0,7,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(177,2,2,6,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"north\": [6, 6], \"west\": [5, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(178,2,2,7,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [7, 6], \"south\": [7, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(179,2,2,8,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"south\": [8, 8], \"east\": [9, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(180,2,2,9,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"north\": [9, 6], \"west\": [8, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(181,2,2,0,8,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"south\": [0, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(182,2,2,1,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"south\": [1, 9], \"east\": [2, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(183,2,2,2,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"north\": [2, 7], \"west\": [1, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(184,2,2,3,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"north\": [3, 7], \"east\": [4, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(185,2,2,4,8,'You do not notice any hostile presence.\n\nInstead you find a Moogle hiding in the corner...','shop','https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&',NULL,'{\"east\": [5, 8], \"west\": [3, 8]}',0,8,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(186,2,2,5,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [5, 7], \"west\": [4, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(187,2,2,6,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"south\": [6, 9], \"east\": [7, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(188,2,2,7,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"north\": [7, 7], \"west\": [6, 8]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(189,2,2,8,8,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"north\": [8, 7], \"south\": [8, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(190,2,2,9,8,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"south\": [9, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(191,2,2,0,9,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"north\": [0, 8], \"east\": [1, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(192,2,2,1,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"north\": [1, 8], \"east\": [2, 9], \"west\": [0, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(193,2,2,2,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&',NULL,'{\"east\": [3, 9], \"west\": [1, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(194,2,2,3,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&',NULL,'{\"east\": [4, 9], \"west\": [2, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(195,2,2,4,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&',NULL,'{\"east\": [5, 9], \"west\": [3, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(196,2,2,5,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"west\": [4, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(197,2,2,6,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"north\": [6, 8], \"east\": [7, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(198,2,2,7,9,'An enemy appears upon entering the area...','monster','',14,'{\"east\": [8, 9], \"west\": [6, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(199,2,2,8,9,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [8, 8], \"east\": [9, 9], \"west\": [7, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(200,2,2,9,9,'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&',NULL,'{\"north\": [9, 8], \"west\": [8, 9]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:14:04',NULL,NULL),
(201,2,1,0,1,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"north\": [0, 0], \"south\": [0, 2]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:15:11',NULL,NULL),
(202,2,1,0,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&',NULL,'{\"north\": [0, 4], \"south\": [0, 6], \"east\": [1, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:39:45',NULL,NULL),
(203,2,1,1,7,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&',NULL,'{\"north\": [1, 6], \"west\": [0, 7]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:45:47',NULL,NULL),
(204,2,1,5,5,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"east\": [6, 5], \"west\": [4, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:47:41',NULL,NULL),
(205,2,1,7,4,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&',NULL,'{\"north\": [7, 3], \"south\": [7, 5]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:48:41',NULL,NULL),
(206,2,1,9,3,'You do not notice anything of importance, the area appears to be safe.','safe','https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&',NULL,'{\"north\": [9, 2], \"south\": [9, 4]}',0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2025-12-21 01:50:47',NULL,NULL);
/*!40000 ALTER TABLE `rooms` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seed_meta`
--

DROP TABLE IF EXISTS `seed_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `seed_meta` (
  `seed_name` varchar(100) NOT NULL,
  `applied_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`seed_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seed_meta`
--

LOCK TABLES `seed_meta` WRITE;
/*!40000 ALTER TABLE `seed_meta` DISABLE KEYS */;
INSERT INTO `seed_meta` VALUES
('initial_seed','2025-12-20 16:34:38');
/*!40000 ALTER TABLE `seed_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `session_players`
--

DROP TABLE IF EXISTS `session_players`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `session_players` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` int(11) NOT NULL,
  `player_id` bigint(20) NOT NULL,
  `joined_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `session_players_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `session_players`
--

LOCK TABLES `session_players` WRITE;
/*!40000 ALTER TABLE `session_players` DISABLE KEYS */;
INSERT INTO `session_players` VALUES
(1,1,821995310179155999,'2025-12-21 00:14:14'),
(2,2,821995310179155999,'2025-12-21 01:12:56');
/*!40000 ALTER TABLE `session_players` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `session_saves`
--

DROP TABLE IF EXISTS `session_saves`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `session_saves` (
  `session_id` int(11) NOT NULL,
  `slot` int(11) NOT NULL,
  `save_title` varchar(100) NOT NULL,
  `is_auto_save` tinyint(1) NOT NULL DEFAULT 0,
  `saved_state` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`saved_state`)),
  `timestamp` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`session_id`,`slot`),
  CONSTRAINT `session_saves_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `session_saves`
--

LOCK TABLES `session_saves` WRITE;
/*!40000 ALTER TABLE `session_saves` DISABLE KEYS */;
/*!40000 ALTER TABLE `session_saves` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `session_vendor_instances`
--

DROP TABLE IF EXISTS `session_vendor_instances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `session_vendor_instances` (
  `session_vendor_id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` int(11) NOT NULL,
  `vendor_id` int(11) NOT NULL,
  `vendor_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`session_vendor_id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `session_vendor_instances_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `session_vendor_instances`
--

LOCK TABLES `session_vendor_instances` WRITE;
/*!40000 ALTER TABLE `session_vendor_instances` DISABLE KEYS */;
INSERT INTO `session_vendor_instances` VALUES
(1,2,1,'Stiltzkin','__**Stiltzkin:**__\n\n**\"Oh hello, I’m glad to see you are not a monster, kupo! I’m a traveling merchant, see.. I was portal hopping and suddenly came across a black portal I’d never seen before...\"**\n\nStiltzkin looks at you as if he’s trying to recall something. **\"Have we met before, kupo? You seem familiar.\"**\n\n**\"At any rate, if you’d like to buy or sell something the shop is still open.\"**','https://cdn.discordapp.com/attachments/1362832151485354065/1362946279587713074/stiltzkin.gif?ex=68345ce3&is=68330b63&hm=b99988391998062f540188581a94327b15919d6d620bf7fe8dae6a953e29ba24&','2025-12-21 01:14:04'),
(2,2,2,'Artemecion','__**Artemecion:**__\n\n\"Hey you aren\'t a monster, Kupo! Do you need a **Letter** delivered by chance? \n\nNo? Hmph, well I also sell a few wares I find along my journey, kupo.\"\n\n*Artemecion pauses for a moment, it looks as though he\'s trying to recall something...*\n\n\"Sorry... your face reminds me of **someone I haven\'t seen in a long time**, kupo. I was lost in a good memory for a moment. \n\nFeel free to browse, but my dyes are off limits, kupo!\"','https://cdn.discordapp.com/attachments/1362832151485354065/1376308818199445604/Artemecion.gif?ex=6834daf8&is=68338978&hm=16ecf8b4fff715e695e67f6c647a7dc918bf8cfb0486ac383cb337e22f380efd&','2025-12-21 01:14:04'),
(3,2,1,'Stiltzkin','__**Stiltzkin:**__\n\n**\"Oh hello, I’m glad to see you are not a monster, kupo! I’m a traveling merchant, see.. I was portal hopping and suddenly came across a black portal I’d never seen before...\"**\n\nStiltzkin looks at you as if he’s trying to recall something. **\"Have we met before, kupo? You seem familiar.\"**\n\n**\"At any rate, if you’d like to buy or sell something the shop is still open.\"**','https://cdn.discordapp.com/attachments/1362832151485354065/1362946279587713074/stiltzkin.gif?ex=68345ce3&is=68330b63&hm=b99988391998062f540188581a94327b15919d6d620bf7fe8dae6a953e29ba24&','2025-12-21 01:14:04'),
(4,2,1,'Stiltzkin','__**Stiltzkin:**__\n\n**\"Oh hello, I’m glad to see you are not a monster, kupo! I’m a traveling merchant, see.. I was portal hopping and suddenly came across a black portal I’d never seen before...\"**\n\nStiltzkin looks at you as if he’s trying to recall something. **\"Have we met before, kupo? You seem familiar.\"**\n\n**\"At any rate, if you’d like to buy or sell something the shop is still open.\"**','https://cdn.discordapp.com/attachments/1362832151485354065/1362946279587713074/stiltzkin.gif?ex=68345ce3&is=68330b63&hm=b99988391998062f540188581a94327b15919d6d620bf7fe8dae6a953e29ba24&','2025-12-21 01:14:04'),
(5,2,2,'Artemecion','__**Artemecion:**__\n\n\"Hey you aren\'t a monster, Kupo! Do you need a **Letter** delivered by chance? \n\nNo? Hmph, well I also sell a few wares I find along my journey, kupo.\"\n\n*Artemecion pauses for a moment, it looks as though he\'s trying to recall something...*\n\n\"Sorry... your face reminds me of **someone I haven\'t seen in a long time**, kupo. I was lost in a good memory for a moment. \n\nFeel free to browse, but my dyes are off limits, kupo!\"','https://cdn.discordapp.com/attachments/1362832151485354065/1376308818199445604/Artemecion.gif?ex=6834daf8&is=68338978&hm=16ecf8b4fff715e695e67f6c647a7dc918bf8cfb0486ac383cb337e22f380efd&','2025-12-21 01:14:04'),
(6,2,2,'Artemecion','__**Artemecion:**__\n\n\"Hey you aren\'t a monster, Kupo! Do you need a **Letter** delivered by chance? \n\nNo? Hmph, well I also sell a few wares I find along my journey, kupo.\"\n\n*Artemecion pauses for a moment, it looks as though he\'s trying to recall something...*\n\n\"Sorry... your face reminds me of **someone I haven\'t seen in a long time**, kupo. I was lost in a good memory for a moment. \n\nFeel free to browse, but my dyes are off limits, kupo!\"','https://cdn.discordapp.com/attachments/1362832151485354065/1376308818199445604/Artemecion.gif?ex=6834daf8&is=68338978&hm=16ecf8b4fff715e695e67f6c647a7dc918bf8cfb0486ac383cb337e22f380efd&','2025-12-21 01:14:04'),
(7,2,1,'Stiltzkin','__**Stiltzkin:**__\n\n**\"Oh hello, I’m glad to see you are not a monster, kupo! I’m a traveling merchant, see.. I was portal hopping and suddenly came across a black portal I’d never seen before...\"**\n\nStiltzkin looks at you as if he’s trying to recall something. **\"Have we met before, kupo? You seem familiar.\"**\n\n**\"At any rate, if you’d like to buy or sell something the shop is still open.\"**','https://cdn.discordapp.com/attachments/1362832151485354065/1362946279587713074/stiltzkin.gif?ex=68345ce3&is=68330b63&hm=b99988391998062f540188581a94327b15919d6d620bf7fe8dae6a953e29ba24&','2025-12-21 01:14:04'),
(8,2,1,'Stiltzkin','__**Stiltzkin:**__\n\n**\"Oh hello, I’m glad to see you are not a monster, kupo! I’m a traveling merchant, see.. I was portal hopping and suddenly came across a black portal I’d never seen before...\"**\n\nStiltzkin looks at you as if he’s trying to recall something. **\"Have we met before, kupo? You seem familiar.\"**\n\n**\"At any rate, if you’d like to buy or sell something the shop is still open.\"**','https://cdn.discordapp.com/attachments/1362832151485354065/1362946279587713074/stiltzkin.gif?ex=68345ce3&is=68330b63&hm=b99988391998062f540188581a94327b15919d6d620bf7fe8dae6a953e29ba24&','2025-12-21 01:14:04');
/*!40000 ALTER TABLE `session_vendor_instances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `session_vendor_items`
--

DROP TABLE IF EXISTS `session_vendor_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `session_vendor_items` (
  `session_vendor_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `price` int(11) DEFAULT 0,
  `stock` int(11) DEFAULT NULL,
  `instance_stock` int(11) DEFAULT NULL,
  `session_id` int(11) NOT NULL,
  PRIMARY KEY (`session_vendor_id`,`item_id`),
  KEY `item_id` (`item_id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `session_vendor_items_ibfk_1` FOREIGN KEY (`session_vendor_id`) REFERENCES `session_vendor_instances` (`session_vendor_id`) ON DELETE CASCADE,
  CONSTRAINT `session_vendor_items_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE CASCADE,
  CONSTRAINT `session_vendor_items_ibfk_3` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `session_vendor_items`
--

LOCK TABLES `session_vendor_items` WRITE;
/*!40000 ALTER TABLE `session_vendor_items` DISABLE KEYS */;
INSERT INTO `session_vendor_items` VALUES
(1,1,50,3,2,2),
(1,3,100,3,1,2),
(1,4,500,3,3,2),
(2,4,500,2,3,2),
(2,5,500,10,10,2),
(2,9,150,3,3,2),
(3,1,50,3,2,2),
(3,3,100,3,1,2),
(3,4,500,3,3,2),
(4,1,50,3,2,2),
(4,3,100,3,1,2),
(4,4,500,3,3,2),
(5,4,500,3,3,2),
(5,5,500,10,10,2),
(5,9,150,3,3,2),
(6,4,500,3,3,2),
(6,5,500,10,10,2),
(6,9,150,3,3,2),
(7,1,50,3,2,2),
(7,3,100,3,1,2),
(7,4,500,3,3,2),
(8,1,50,3,2,2),
(8,3,100,3,1,2),
(8,4,500,3,3,2);
/*!40000 ALTER TABLE `session_vendor_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sessions`
--

DROP TABLE IF EXISTS `sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sessions` (
  `session_id` int(11) NOT NULL AUTO_INCREMENT,
  `guild_id` bigint(20) NOT NULL,
  `thread_id` varchar(64) NOT NULL,
  `owner_id` bigint(20) NOT NULL,
  `num_players` int(11) NOT NULL,
  `current_turn` bigint(20) DEFAULT NULL,
  `player_turn` bigint(20) DEFAULT NULL,
  `status` enum('active','paused','ended') DEFAULT 'active',
  `saved` tinyint(1) NOT NULL DEFAULT 0,
  `current_floor` int(11) DEFAULT 1,
  `total_floors` int(11) DEFAULT 1,
  `difficulty` varchar(50) DEFAULT NULL,
  `message_id` bigint(20) DEFAULT NULL,
  `game_log` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`game_log`)),
  `game_state` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`game_state`)),
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`session_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sessions`
--

LOCK TABLES `sessions` WRITE;
/*!40000 ALTER TABLE `sessions` DISABLE KEYS */;
INSERT INTO `sessions` VALUES
(1,1337786582996095036,'1452091762020712450',821995310179155999,1,NULL,NULL,'active',0,1,1,'Easy',NULL,'[\"Difficulty set to **Easy**.\", \"<@821995310179155999> chose **Summoner**.\"]',NULL,'2025-12-21 00:14:14','2025-12-21 00:14:46'),
(2,1337786582996095036,'1452106531914125438',821995310179155999,1,NULL,NULL,'active',0,1,2,'Easy',NULL,'[\"<@821995310179155999> moved north.\", \"<@821995310179155999> moved north.\", \"<@821995310179155999> moved east.\", \"<@821995310179155999> moved south.\", \"<@821995310179155999> moved south.\", \"Encountered **Tonberry Chef**!\", \"Tonberry Chef was defeated!\", \"<@821995310179155999> moved south.\", \"Cure restores 106 HP.\", \"You are healed to 411\\u202fHP.\"]','{\"difficulty\": \"Easy\", \"total_floors\": 2, \"rooms\": [{\"floor_id\": 1, \"x\": 0, \"y\": 0, \"type\": \"entrance\", \"exits\": {\"south\": [0, 1]}}, {\"floor_id\": 1, \"x\": 1, \"y\": 0, \"type\": \"cloister\", \"exits\": {\"south\": [1, 1]}}, {\"floor_id\": 1, \"x\": 2, \"y\": 0, \"type\": \"cloister\", \"exits\": {\"south\": [2, 1], \"east\": [3, 0]}}, {\"floor_id\": 1, \"x\": 3, \"y\": 0, \"type\": \"cloister\", \"exits\": {\"south\": [3, 1], \"west\": [2, 0]}}, {\"floor_id\": 1, \"x\": 4, \"y\": 0, \"type\": \"monster\", \"exits\": {\"south\": [4, 1], \"east\": [5, 0]}}, {\"floor_id\": 1, \"x\": 5, \"y\": 0, \"type\": \"safe\", \"exits\": {\"east\": [6, 0], \"west\": [4, 0]}}, {\"floor_id\": 1, \"x\": 6, \"y\": 0, \"type\": \"safe\", \"exits\": {\"east\": [7, 0], \"west\": [5, 0]}}, {\"floor_id\": 1, \"x\": 7, \"y\": 0, \"type\": \"safe\", \"exits\": {\"east\": [8, 0], \"west\": [6, 0]}}, {\"floor_id\": 1, \"x\": 8, \"y\": 0, \"type\": \"shop\", \"exits\": {\"east\": [9, 0], \"west\": [7, 0]}}, {\"floor_id\": 1, \"x\": 9, \"y\": 0, \"type\": \"safe\", \"exits\": {\"south\": [9, 1], \"west\": [8, 0]}}, {\"floor_id\": 1, \"x\": 0, \"y\": 1, \"type\": \"monster\", \"exits\": {\"north\": [0, 0], \"south\": [0, 2]}}, {\"floor_id\": 1, \"x\": 1, \"y\": 1, \"type\": \"monster\", \"exits\": {\"north\": [1, 0], \"east\": [2, 1]}}, {\"floor_id\": 1, \"x\": 2, \"y\": 1, \"type\": \"safe\", \"exits\": {\"north\": [2, 0], \"south\": [2, 2], \"east\": [3, 1], \"west\": [1, 1]}}, {\"floor_id\": 1, \"x\": 3, \"y\": 1, \"type\": \"safe\", \"exits\": {\"north\": [3, 0], \"south\": [3, 2], \"west\": [2, 1]}}, {\"floor_id\": 1, \"x\": 4, \"y\": 1, \"type\": \"safe\", \"exits\": {\"north\": [4, 0], \"east\": [5, 1]}}, {\"floor_id\": 1, \"x\": 5, \"y\": 1, \"type\": \"illusion\", \"exits\": {\"east\": [6, 1], \"west\": [4, 1]}}, {\"floor_id\": 1, \"x\": 6, \"y\": 1, \"type\": \"safe\", \"exits\": {\"east\": [7, 1], \"west\": [5, 1]}}, {\"floor_id\": 1, \"x\": 7, \"y\": 1, \"type\": \"safe\", \"exits\": {\"south\": [7, 2], \"west\": [6, 1]}}, {\"floor_id\": 1, \"x\": 8, \"y\": 1, \"type\": \"safe\", \"exits\": {\"south\": [8, 2], \"east\": [9, 1]}}, {\"floor_id\": 1, \"x\": 9, \"y\": 1, \"type\": \"safe\", \"exits\": {\"north\": [9, 0], \"south\": [9, 2], \"west\": [8, 1]}}, {\"floor_id\": 1, \"x\": 0, \"y\": 2, \"type\": \"safe\", \"exits\": {\"north\": [0, 1], \"east\": [1, 2]}}, {\"floor_id\": 1, \"x\": 1, \"y\": 2, \"type\": \"safe\", \"exits\": {\"south\": [1, 3], \"west\": [0, 2]}}, {\"floor_id\": 1, \"x\": 2, \"y\": 2, \"type\": \"safe\", \"exits\": {\"north\": [2, 1]}}, {\"floor_id\": 1, \"x\": 3, \"y\": 2, \"type\": \"monster\", \"exits\": {\"north\": [3, 1], \"south\": [3, 3]}}, {\"floor_id\": 1, \"x\": 4, \"y\": 2, \"type\": \"monster\", \"exits\": {\"south\": [4, 3], \"east\": [5, 2]}}, {\"floor_id\": 1, \"x\": 5, \"y\": 2, \"type\": \"safe\", \"exits\": {\"east\": [6, 2], \"west\": [4, 2]}}, {\"floor_id\": 1, \"x\": 6, \"y\": 2, \"type\": \"safe\", \"exits\": {\"east\": [7, 2], \"west\": [5, 2]}}, {\"floor_id\": 1, \"x\": 7, \"y\": 2, \"type\": \"monster\", \"exits\": {\"north\": [7, 1], \"west\": [6, 2]}}, {\"floor_id\": 1, \"x\": 8, \"y\": 2, \"type\": \"shop\", \"exits\": {\"north\": [8, 1], \"south\": [8, 3]}}, {\"floor_id\": 1, \"x\": 9, \"y\": 2, \"type\": \"safe\", \"exits\": {\"north\": [9, 1], \"south\": [9, 3]}}, {\"floor_id\": 1, \"x\": 0, \"y\": 3, \"type\": \"safe\", \"exits\": {\"south\": [0, 4]}}, {\"floor_id\": 1, \"x\": 1, \"y\": 3, \"type\": \"safe\", \"exits\": {\"north\": [1, 2], \"east\": [2, 3]}}, {\"floor_id\": 1, \"x\": 2, \"y\": 3, \"type\": \"shop\", \"exits\": {\"south\": [2, 4], \"west\": [1, 3]}}, {\"floor_id\": 1, \"x\": 3, \"y\": 3, \"type\": \"safe\", \"exits\": {\"north\": [3, 2], \"south\": [3, 4]}}, {\"floor_id\": 1, \"x\": 4, \"y\": 3, \"type\": \"monster\", \"exits\": {\"north\": [4, 2], \"east\": [5, 3]}}, {\"floor_id\": 1, \"x\": 5, \"y\": 3, \"type\": \"safe\", \"exits\": {\"east\": [6, 3], \"west\": [4, 3]}}, {\"floor_id\": 1, \"x\": 6, \"y\": 3, \"type\": \"safe\", \"exits\": {\"south\": [6, 4], \"west\": [5, 3]}}, {\"floor_id\": 1, \"x\": 7, \"y\": 3, \"type\": \"safe\", \"exits\": {\"south\": [7, 4], \"east\": [8, 3]}}, {\"floor_id\": 1, \"x\": 8, \"y\": 3, \"type\": \"safe\", \"exits\": {\"north\": [8, 2], \"west\": [7, 3]}}, {\"floor_id\": 1, \"x\": 9, \"y\": 3, \"type\": \"monster\", \"exits\": {\"north\": [9, 2], \"south\": [9, 4]}}, {\"floor_id\": 1, \"x\": 0, \"y\": 4, \"type\": \"shop\", \"exits\": {\"north\": [0, 3], \"south\": [0, 5], \"east\": [1, 4]}}, {\"floor_id\": 1, \"x\": 1, \"y\": 4, \"type\": \"safe\", \"exits\": {\"east\": [2, 4], \"west\": [0, 4]}}, {\"floor_id\": 1, \"x\": 2, \"y\": 4, \"type\": \"safe\", \"exits\": {\"north\": [2, 3], \"west\": [1, 4]}}, {\"floor_id\": 1, \"x\": 3, \"y\": 4, \"type\": \"safe\", \"exits\": {\"north\": [3, 3], \"east\": [4, 4]}}, {\"floor_id\": 1, \"x\": 4, \"y\": 4, \"type\": \"safe\", \"exits\": {\"east\": [5, 4], \"west\": [3, 4]}}, {\"floor_id\": 1, \"x\": 5, \"y\": 4, \"type\": \"safe\", \"exits\": {\"east\": [6, 4], \"west\": [4, 4]}}, {\"floor_id\": 1, \"x\": 6, \"y\": 4, \"type\": \"monster\", \"exits\": {\"north\": [6, 3], \"west\": [5, 4]}}, {\"floor_id\": 1, \"x\": 7, \"y\": 4, \"type\": \"monster\", \"exits\": {\"north\": [7, 3], \"south\": [7, 5]}}, {\"floor_id\": 1, \"x\": 8, \"y\": 4, \"type\": \"safe\", \"exits\": {\"south\": [8, 5]}}, {\"floor_id\": 1, \"x\": 9, \"y\": 4, \"type\": \"safe\", \"exits\": {\"north\": [9, 3], \"south\": [9, 5]}}, {\"floor_id\": 1, \"x\": 0, \"y\": 5, \"type\": \"monster\", \"exits\": {\"north\": [0, 4], \"south\": [0, 6], \"east\": [1, 5]}}, {\"floor_id\": 1, \"x\": 1, \"y\": 5, \"type\": \"safe\", \"exits\": {\"east\": [2, 5], \"west\": [0, 5]}}, {\"floor_id\": 1, \"x\": 2, \"y\": 5, \"type\": \"safe\", \"exits\": {\"south\": [2, 6], \"east\": [3, 5], \"west\": [1, 5]}}, {\"floor_id\": 1, \"x\": 3, \"y\": 5, \"type\": \"safe\", \"exits\": {\"east\": [4, 5], \"west\": [2, 5]}}, {\"floor_id\": 1, \"x\": 4, \"y\": 5, \"type\": \"safe\", \"exits\": {\"east\": [5, 5], \"west\": [3, 5]}}, {\"floor_id\": 1, \"x\": 5, \"y\": 5, \"type\": \"monster\", \"exits\": {\"east\": [6, 5], \"west\": [4, 5]}}, {\"floor_id\": 1, \"x\": 6, \"y\": 5, \"type\": \"safe\", \"exits\": {\"east\": [7, 5], \"west\": [5, 5]}}, {\"floor_id\": 1, \"x\": 7, \"y\": 5, \"type\": \"safe\", \"exits\": {\"north\": [7, 4], \"west\": [6, 5]}}, {\"floor_id\": 1, \"x\": 8, \"y\": 5, \"type\": \"safe\", \"exits\": {\"north\": [8, 4], \"south\": [8, 6]}}, {\"floor_id\": 1, \"x\": 9, \"y\": 5, \"type\": \"monster\", \"exits\": {\"north\": [9, 4], \"south\": [9, 6]}}, {\"floor_id\": 1, \"x\": 0, \"y\": 6, \"type\": \"locked\", \"exits\": {\"north\": [0, 5], \"south\": [0, 7]}}, {\"floor_id\": 1, \"x\": 1, \"y\": 6, \"type\": \"safe\", \"exits\": {\"south\": [1, 7], \"east\": [2, 6]}}, {\"floor_id\": 1, \"x\": 2, \"y\": 6, \"type\": \"safe\", \"exits\": {\"north\": [2, 5], \"west\": [1, 6]}}, {\"floor_id\": 1, \"x\": 3, \"y\": 6, \"type\": \"safe\", \"exits\": {\"east\": [4, 6]}}, {\"floor_id\": 1, \"x\": 4, \"y\": 6, \"type\": \"safe\", \"exits\": {\"south\": [4, 7], \"east\": [5, 6], \"west\": [3, 6]}}, {\"floor_id\": 1, \"x\": 5, \"y\": 6, \"type\": \"monster\", \"exits\": {\"south\": [5, 7], \"west\": [4, 6]}}, {\"floor_id\": 1, \"x\": 6, \"y\": 6, \"type\": \"safe\", \"exits\": {\"south\": [6, 7], \"east\": [7, 6]}}, {\"floor_id\": 1, \"x\": 7, \"y\": 6, \"type\": \"safe\", \"exits\": {\"south\": [7, 7], \"east\": [8, 6], \"west\": [6, 6]}}, {\"floor_id\": 1, \"x\": 8, \"y\": 6, \"type\": \"monster\", \"exits\": {\"north\": [8, 5], \"west\": [7, 6]}}, {\"floor_id\": 1, \"x\": 9, \"y\": 6, \"type\": \"monster\", \"exits\": {\"north\": [9, 5], \"south\": [9, 7]}}, {\"floor_id\": 1, \"x\": 0, \"y\": 7, \"type\": \"item\", \"exits\": {\"north\": [0, 6], \"east\": [1, 7]}}, {\"floor_id\": 1, \"x\": 1, \"y\": 7, \"type\": \"monster\", \"exits\": {\"north\": [1, 6], \"west\": [0, 7]}}, {\"floor_id\": 1, \"x\": 2, \"y\": 7, \"type\": \"safe\", \"exits\": {\"south\": [2, 8], \"east\": [3, 7]}}, {\"floor_id\": 1, \"x\": 3, \"y\": 7, \"type\": \"monster\", \"exits\": {\"south\": [3, 8], \"east\": [4, 7], \"west\": [2, 7]}}, {\"floor_id\": 1, \"x\": 4, \"y\": 7, \"type\": \"safe\", \"exits\": {\"north\": [4, 6], \"west\": [3, 7]}}, {\"floor_id\": 1, \"x\": 5, \"y\": 7, \"type\": \"safe\", \"exits\": {\"north\": [5, 6]}}, {\"floor_id\": 1, \"x\": 6, \"y\": 7, \"type\": \"safe\", \"exits\": {\"north\": [6, 6], \"south\": [6, 8]}}, {\"floor_id\": 1, \"x\": 7, \"y\": 7, \"type\": \"safe\", \"exits\": {\"north\": [7, 6], \"east\": [8, 7]}}, {\"floor_id\": 1, \"x\": 8, \"y\": 7, \"type\": \"illusion\", \"exits\": {\"east\": [9, 7], \"west\": [7, 7]}}, {\"floor_id\": 1, \"x\": 9, \"y\": 7, \"type\": \"safe\", \"exits\": {\"north\": [9, 6], \"south\": [9, 8], \"west\": [8, 7]}}, {\"floor_id\": 1, \"x\": 0, \"y\": 8, \"type\": \"safe\", \"exits\": {\"south\": [0, 9]}}, {\"floor_id\": 1, \"x\": 1, \"y\": 8, \"type\": \"illusion\", \"exits\": {\"south\": [1, 9], \"east\": [2, 8]}}, {\"floor_id\": 1, \"x\": 2, \"y\": 8, \"type\": \"monster\", \"exits\": {\"north\": [2, 7], \"south\": [2, 9], \"west\": [1, 8]}}, {\"floor_id\": 1, \"x\": 3, \"y\": 8, \"type\": \"safe\", \"exits\": {\"north\": [3, 7]}}, {\"floor_id\": 1, \"x\": 4, \"y\": 8, \"type\": \"safe\", \"exits\": {\"south\": [4, 9], \"east\": [5, 8]}}, {\"floor_id\": 1, \"x\": 5, \"y\": 8, \"type\": \"monster\", \"exits\": {\"east\": [6, 8], \"west\": [4, 8]}}, {\"floor_id\": 1, \"x\": 6, \"y\": 8, \"type\": \"safe\", \"exits\": {\"north\": [6, 7], \"west\": [5, 8]}}, {\"floor_id\": 1, \"x\": 7, \"y\": 8, \"type\": \"monster\", \"exits\": {\"east\": [8, 8]}}, {\"floor_id\": 1, \"x\": 8, \"y\": 8, \"type\": \"safe\", \"exits\": {\"east\": [9, 8], \"west\": [7, 8]}}, {\"floor_id\": 1, \"x\": 9, \"y\": 8, \"type\": \"monster\", \"exits\": {\"north\": [9, 7], \"south\": [9, 9], \"west\": [8, 8]}}, {\"floor_id\": 1, \"x\": 0, \"y\": 9, \"type\": \"safe\", \"exits\": {\"north\": [0, 8], \"east\": [1, 9]}}, {\"floor_id\": 1, \"x\": 1, \"y\": 9, \"type\": \"monster\", \"exits\": {\"north\": [1, 8], \"west\": [0, 9]}}, {\"floor_id\": 1, \"x\": 2, \"y\": 9, \"type\": \"monster\", \"exits\": {\"north\": [2, 8], \"east\": [3, 9]}}, {\"floor_id\": 1, \"x\": 3, \"y\": 9, \"type\": \"monster\", \"exits\": {\"east\": [4, 9], \"west\": [2, 9]}}, {\"floor_id\": 1, \"x\": 4, \"y\": 9, \"type\": \"monster\", \"exits\": {\"north\": [4, 8], \"east\": [5, 9], \"west\": [3, 9]}}, {\"floor_id\": 1, \"x\": 5, \"y\": 9, \"type\": \"safe\", \"exits\": {\"east\": [6, 9], \"west\": [4, 9]}}, {\"floor_id\": 1, \"x\": 6, \"y\": 9, \"type\": \"safe\", \"exits\": {\"east\": [7, 9], \"west\": [5, 9]}}, {\"floor_id\": 1, \"x\": 7, \"y\": 9, \"type\": \"safe\", \"exits\": {\"east\": [8, 9], \"west\": [6, 9]}}, {\"floor_id\": 1, \"x\": 8, \"y\": 9, \"type\": \"safe\", \"exits\": {\"east\": [9, 9], \"west\": [7, 9]}}, {\"floor_id\": 1, \"x\": 9, \"y\": 9, \"type\": \"monster\", \"exits\": {\"north\": [9, 8], \"west\": [8, 9]}}, {\"floor_id\": 2, \"x\": 0, \"y\": 0, \"type\": \"safe\", \"exits\": {\"east\": [1, 0]}}, {\"floor_id\": 2, \"x\": 1, \"y\": 0, \"type\": \"safe\", \"exits\": {\"south\": [1, 1], \"west\": [0, 0]}}, {\"floor_id\": 2, \"x\": 2, \"y\": 0, \"type\": \"safe\", \"exits\": {\"south\": [2, 1], \"east\": [3, 0]}}, {\"floor_id\": 2, \"x\": 3, \"y\": 0, \"type\": \"safe\", \"exits\": {\"south\": [3, 1], \"west\": [2, 0]}}, {\"floor_id\": 2, \"x\": 4, \"y\": 0, \"type\": \"monster\", \"exits\": {\"south\": [4, 1], \"east\": [5, 0]}}, {\"floor_id\": 2, \"x\": 5, \"y\": 0, \"type\": \"boss\", \"exits\": {\"east\": [6, 0], \"west\": [4, 0]}}, {\"floor_id\": 2, \"x\": 6, \"y\": 0, \"type\": \"illusion\", \"exits\": {\"east\": [7, 0], \"west\": [5, 0]}}, {\"floor_id\": 2, \"x\": 7, \"y\": 0, \"type\": \"safe\", \"exits\": {\"south\": [7, 1], \"west\": [6, 0]}}, {\"floor_id\": 2, \"x\": 8, \"y\": 0, \"type\": \"monster\", \"exits\": {\"south\": [8, 1], \"east\": [9, 0]}}, {\"floor_id\": 2, \"x\": 9, \"y\": 0, \"type\": \"monster\", \"exits\": {\"west\": [8, 0]}}, {\"floor_id\": 2, \"x\": 0, \"y\": 1, \"type\": \"safe\", \"exits\": {\"south\": [0, 2]}}, {\"floor_id\": 2, \"x\": 1, \"y\": 1, \"type\": \"shop\", \"exits\": {\"north\": [1, 0], \"south\": [1, 2]}}, {\"floor_id\": 2, \"x\": 2, \"y\": 1, \"type\": \"safe\", \"exits\": {\"north\": [2, 0], \"south\": [2, 2]}}, {\"floor_id\": 2, \"x\": 3, \"y\": 1, \"type\": \"safe\", \"exits\": {\"north\": [3, 0], \"east\": [4, 1]}}, {\"floor_id\": 2, \"x\": 4, \"y\": 1, \"type\": \"shop\", \"exits\": {\"north\": [4, 0], \"west\": [3, 1]}}, {\"floor_id\": 2, \"x\": 5, \"y\": 1, \"type\": \"safe\", \"exits\": {\"south\": [5, 2], \"east\": [6, 1]}}, {\"floor_id\": 2, \"x\": 6, \"y\": 1, \"type\": \"safe\", \"exits\": {\"east\": [7, 1], \"west\": [5, 1]}}, {\"floor_id\": 2, \"x\": 7, \"y\": 1, \"type\": \"safe\", \"exits\": {\"north\": [7, 0], \"west\": [6, 1]}}, {\"floor_id\": 2, \"x\": 8, \"y\": 1, \"type\": \"safe\", \"exits\": {\"north\": [8, 0], \"east\": [9, 1]}}, {\"floor_id\": 2, \"x\": 9, \"y\": 1, \"type\": \"safe\", \"exits\": {\"south\": [9, 2], \"west\": [8, 1]}}, {\"floor_id\": 2, \"x\": 0, \"y\": 2, \"type\": \"monster\", \"exits\": {\"north\": [0, 1], \"south\": [0, 3], \"east\": [1, 2]}}, {\"floor_id\": 2, \"x\": 1, \"y\": 2, \"type\": \"safe\", \"exits\": {\"north\": [1, 1], \"west\": [0, 2]}}, {\"floor_id\": 2, \"x\": 2, \"y\": 2, \"type\": \"safe\", \"exits\": {\"north\": [2, 1], \"south\": [2, 3]}}, {\"floor_id\": 2, \"x\": 3, \"y\": 2, \"type\": \"safe\", \"exits\": {\"east\": [4, 2]}}, {\"floor_id\": 2, \"x\": 4, \"y\": 2, \"type\": \"monster\", \"exits\": {\"east\": [5, 2], \"west\": [3, 2]}}, {\"floor_id\": 2, \"x\": 5, \"y\": 2, \"type\": \"safe\", \"exits\": {\"north\": [5, 1], \"east\": [6, 2], \"west\": [4, 2]}}, {\"floor_id\": 2, \"x\": 6, \"y\": 2, \"type\": \"monster\", \"exits\": {\"east\": [7, 2], \"west\": [5, 2]}}, {\"floor_id\": 2, \"x\": 7, \"y\": 2, \"type\": \"monster\", \"exits\": {\"east\": [8, 2], \"west\": [6, 2]}}, {\"floor_id\": 2, \"x\": 8, \"y\": 2, \"type\": \"safe\", \"exits\": {\"east\": [9, 2], \"west\": [7, 2]}}, {\"floor_id\": 2, \"x\": 9, \"y\": 2, \"type\": \"safe\", \"exits\": {\"north\": [9, 1], \"south\": [9, 3], \"west\": [8, 2]}}, {\"floor_id\": 2, \"x\": 0, \"y\": 3, \"type\": \"monster\", \"exits\": {\"north\": [0, 2], \"south\": [0, 4], \"east\": [1, 3]}}, {\"floor_id\": 2, \"x\": 1, \"y\": 3, \"type\": \"safe\", \"exits\": {\"south\": [1, 4], \"east\": [2, 3], \"west\": [0, 3]}}, {\"floor_id\": 2, \"x\": 2, \"y\": 3, \"type\": \"monster\", \"exits\": {\"north\": [2, 2], \"east\": [3, 3], \"west\": [1, 3]}}, {\"floor_id\": 2, \"x\": 3, \"y\": 3, \"type\": \"safe\", \"exits\": {\"east\": [4, 3], \"west\": [2, 3]}}, {\"floor_id\": 2, \"x\": 4, \"y\": 3, \"type\": \"safe\", \"exits\": {\"south\": [4, 4], \"west\": [3, 3]}}, {\"floor_id\": 2, \"x\": 5, \"y\": 3, \"type\": \"safe\", \"exits\": {\"south\": [5, 4], \"east\": [6, 3]}}, {\"floor_id\": 2, \"x\": 6, \"y\": 3, \"type\": \"boss\", \"exits\": {\"east\": [7, 3], \"west\": [5, 3]}}, {\"floor_id\": 2, \"x\": 7, \"y\": 3, \"type\": \"exit\", \"exits\": {\"south\": [7, 4], \"east\": [8, 3], \"west\": [6, 3]}}, {\"floor_id\": 2, \"x\": 8, \"y\": 3, \"type\": \"monster\", \"exits\": {\"south\": [8, 4], \"west\": [7, 3]}}, {\"floor_id\": 2, \"x\": 9, \"y\": 3, \"type\": \"safe\", \"exits\": {\"north\": [9, 2], \"south\": [9, 4]}}, {\"floor_id\": 2, \"x\": 0, \"y\": 4, \"type\": \"safe\", \"exits\": {\"north\": [0, 3], \"south\": [0, 5]}}, {\"floor_id\": 2, \"x\": 1, \"y\": 4, \"type\": \"safe\", \"exits\": {\"north\": [1, 3], \"south\": [1, 5]}}, {\"floor_id\": 2, \"x\": 2, \"y\": 4, \"type\": \"safe\", \"exits\": {\"south\": [2, 5], \"east\": [3, 4]}}, {\"floor_id\": 2, \"x\": 3, \"y\": 4, \"type\": \"safe\", \"exits\": {\"south\": [3, 5], \"west\": [2, 4]}}, {\"floor_id\": 2, \"x\": 4, \"y\": 4, \"type\": \"safe\", \"exits\": {\"north\": [4, 3], \"south\": [4, 5]}}, {\"floor_id\": 2, \"x\": 5, \"y\": 4, \"type\": \"safe\", \"exits\": {\"north\": [5, 3], \"south\": [5, 5]}}, {\"floor_id\": 2, \"x\": 6, \"y\": 4, \"type\": \"monster\", \"exits\": {\"south\": [6, 5]}}, {\"floor_id\": 2, \"x\": 7, \"y\": 4, \"type\": \"safe\", \"exits\": {\"north\": [7, 3], \"south\": [7, 5]}}, {\"floor_id\": 2, \"x\": 8, \"y\": 4, \"type\": \"cloister\", \"exits\": {\"north\": [8, 3]}}, {\"floor_id\": 2, \"x\": 9, \"y\": 4, \"type\": \"safe\", \"exits\": {\"north\": [9, 3], \"south\": [9, 5]}}, {\"floor_id\": 2, \"x\": 0, \"y\": 5, \"type\": \"monster\", \"exits\": {\"north\": [0, 4], \"south\": [0, 6]}}, {\"floor_id\": 2, \"x\": 1, \"y\": 5, \"type\": \"safe\", \"exits\": {\"north\": [1, 4], \"east\": [2, 5]}}, {\"floor_id\": 2, \"x\": 2, \"y\": 5, \"type\": \"safe\", \"exits\": {\"north\": [2, 4], \"south\": [2, 6], \"west\": [1, 5]}}, {\"floor_id\": 2, \"x\": 3, \"y\": 5, \"type\": \"safe\", \"exits\": {\"north\": [3, 4], \"south\": [3, 6]}}, {\"floor_id\": 2, \"x\": 4, \"y\": 5, \"type\": \"safe\", \"exits\": {\"north\": [4, 4], \"south\": [4, 6]}}, {\"floor_id\": 2, \"x\": 5, \"y\": 5, \"type\": \"safe\", \"exits\": {\"north\": [5, 4], \"south\": [5, 6]}}, {\"floor_id\": 2, \"x\": 6, \"y\": 5, \"type\": \"safe\", \"exits\": {\"north\": [6, 4], \"south\": [6, 6]}}, {\"floor_id\": 2, \"x\": 7, \"y\": 5, \"type\": \"safe\", \"exits\": {\"north\": [7, 4], \"east\": [8, 5]}}, {\"floor_id\": 2, \"x\": 8, \"y\": 5, \"type\": \"safe\", \"exits\": {\"south\": [8, 6], \"west\": [7, 5]}}, {\"floor_id\": 2, \"x\": 9, \"y\": 5, \"type\": \"safe\", \"exits\": {\"north\": [9, 4], \"south\": [9, 6]}}, {\"floor_id\": 2, \"x\": 0, \"y\": 6, \"type\": \"safe\", \"exits\": {\"north\": [0, 5], \"south\": [0, 7]}}, {\"floor_id\": 2, \"x\": 1, \"y\": 6, \"type\": \"safe\", \"exits\": {\"south\": [1, 7], \"east\": [2, 6]}}, {\"floor_id\": 2, \"x\": 2, \"y\": 6, \"type\": \"safe\", \"exits\": {\"north\": [2, 5], \"west\": [1, 6]}}, {\"floor_id\": 2, \"x\": 3, \"y\": 6, \"type\": \"safe\", \"exits\": {\"north\": [3, 5], \"south\": [3, 7], \"east\": [4, 6]}}, {\"floor_id\": 2, \"x\": 4, \"y\": 6, \"type\": \"safe\", \"exits\": {\"north\": [4, 5], \"west\": [3, 6]}}, {\"floor_id\": 2, \"x\": 5, \"y\": 6, \"type\": \"safe\", \"exits\": {\"north\": [5, 5], \"south\": [5, 7], \"east\": [6, 6]}}, {\"floor_id\": 2, \"x\": 6, \"y\": 6, \"type\": \"safe\", \"exits\": {\"north\": [6, 5], \"south\": [6, 7], \"west\": [5, 6]}}, {\"floor_id\": 2, \"x\": 7, \"y\": 6, \"type\": \"safe\", \"exits\": {\"south\": [7, 7], \"east\": [8, 6]}}, {\"floor_id\": 2, \"x\": 8, \"y\": 6, \"type\": \"safe\", \"exits\": {\"north\": [8, 5], \"west\": [7, 6]}}, {\"floor_id\": 2, \"x\": 9, \"y\": 6, \"type\": \"safe\", \"exits\": {\"north\": [9, 5], \"south\": [9, 7]}}, {\"floor_id\": 2, \"x\": 0, \"y\": 7, \"type\": \"staircase_down\", \"exits\": {\"north\": [0, 6], \"east\": [1, 7]}}, {\"floor_id\": 2, \"x\": 1, \"y\": 7, \"type\": \"safe\", \"exits\": {\"north\": [1, 6], \"east\": [2, 7], \"west\": [0, 7]}}, {\"floor_id\": 2, \"x\": 2, \"y\": 7, \"type\": \"safe\", \"exits\": {\"south\": [2, 8], \"east\": [3, 7], \"west\": [1, 7]}}, {\"floor_id\": 2, \"x\": 3, \"y\": 7, \"type\": \"safe\", \"exits\": {\"north\": [3, 6], \"south\": [3, 8], \"east\": [4, 7], \"west\": [2, 7]}}, {\"floor_id\": 2, \"x\": 4, \"y\": 7, \"type\": \"safe\", \"exits\": {\"west\": [3, 7]}}, {\"floor_id\": 2, \"x\": 5, \"y\": 7, \"type\": \"shop\", \"exits\": {\"north\": [5, 6], \"south\": [5, 8], \"east\": [6, 7]}}, {\"floor_id\": 2, \"x\": 6, \"y\": 7, \"type\": \"safe\", \"exits\": {\"north\": [6, 6], \"west\": [5, 7]}}, {\"floor_id\": 2, \"x\": 7, \"y\": 7, \"type\": \"safe\", \"exits\": {\"north\": [7, 6], \"south\": [7, 8]}}, {\"floor_id\": 2, \"x\": 8, \"y\": 7, \"type\": \"safe\", \"exits\": {\"south\": [8, 8], \"east\": [9, 7]}}, {\"floor_id\": 2, \"x\": 9, \"y\": 7, \"type\": \"safe\", \"exits\": {\"north\": [9, 6], \"west\": [8, 7]}}, {\"floor_id\": 2, \"x\": 0, \"y\": 8, \"type\": \"safe\", \"exits\": {\"south\": [0, 9]}}, {\"floor_id\": 2, \"x\": 1, \"y\": 8, \"type\": \"safe\", \"exits\": {\"south\": [1, 9], \"east\": [2, 8]}}, {\"floor_id\": 2, \"x\": 2, \"y\": 8, \"type\": \"safe\", \"exits\": {\"north\": [2, 7], \"west\": [1, 8]}}, {\"floor_id\": 2, \"x\": 3, \"y\": 8, \"type\": \"safe\", \"exits\": {\"north\": [3, 7], \"east\": [4, 8]}}, {\"floor_id\": 2, \"x\": 4, \"y\": 8, \"type\": \"shop\", \"exits\": {\"east\": [5, 8], \"west\": [3, 8]}}, {\"floor_id\": 2, \"x\": 5, \"y\": 8, \"type\": \"safe\", \"exits\": {\"north\": [5, 7], \"west\": [4, 8]}}, {\"floor_id\": 2, \"x\": 6, \"y\": 8, \"type\": \"safe\", \"exits\": {\"south\": [6, 9], \"east\": [7, 8]}}, {\"floor_id\": 2, \"x\": 7, \"y\": 8, \"type\": \"safe\", \"exits\": {\"north\": [7, 7], \"west\": [6, 8]}}, {\"floor_id\": 2, \"x\": 8, \"y\": 8, \"type\": \"safe\", \"exits\": {\"north\": [8, 7], \"south\": [8, 9]}}, {\"floor_id\": 2, \"x\": 9, \"y\": 8, \"type\": \"safe\", \"exits\": {\"south\": [9, 9]}}, {\"floor_id\": 2, \"x\": 0, \"y\": 9, \"type\": \"safe\", \"exits\": {\"north\": [0, 8], \"east\": [1, 9]}}, {\"floor_id\": 2, \"x\": 1, \"y\": 9, \"type\": \"safe\", \"exits\": {\"north\": [1, 8], \"east\": [2, 9], \"west\": [0, 9]}}, {\"floor_id\": 2, \"x\": 2, \"y\": 9, \"type\": \"safe\", \"exits\": {\"east\": [3, 9], \"west\": [1, 9]}}, {\"floor_id\": 2, \"x\": 3, \"y\": 9, \"type\": \"safe\", \"exits\": {\"east\": [4, 9], \"west\": [2, 9]}}, {\"floor_id\": 2, \"x\": 4, \"y\": 9, \"type\": \"safe\", \"exits\": {\"east\": [5, 9], \"west\": [3, 9]}}, {\"floor_id\": 2, \"x\": 5, \"y\": 9, \"type\": \"safe\", \"exits\": {\"west\": [4, 9]}}, {\"floor_id\": 2, \"x\": 6, \"y\": 9, \"type\": \"safe\", \"exits\": {\"north\": [6, 8], \"east\": [7, 9]}}, {\"floor_id\": 2, \"x\": 7, \"y\": 9, \"type\": \"monster\", \"exits\": {\"east\": [8, 9], \"west\": [6, 9]}}, {\"floor_id\": 2, \"x\": 8, \"y\": 9, \"type\": \"safe\", \"exits\": {\"north\": [8, 8], \"east\": [9, 9], \"west\": [7, 9]}}, {\"floor_id\": 2, \"x\": 9, \"y\": 9, \"type\": \"safe\", \"exits\": {\"north\": [9, 8], \"west\": [8, 9]}}], \"width\": 10, \"height\": 10}','2025-12-21 01:12:56','2025-12-21 01:51:09');
/*!40000 ALTER TABLE `sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `status_effects`
--

DROP TABLE IF EXISTS `status_effects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `status_effects` (
  `effect_id` int(11) NOT NULL AUTO_INCREMENT,
  `effect_name` varchar(100) NOT NULL,
  `effect_type` enum('buff','debuff','neutral') NOT NULL,
  `icon_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `value` int(11) NOT NULL,
  `duration` int(11) NOT NULL,
  PRIMARY KEY (`effect_id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `status_effects`
--

LOCK TABLES `status_effects` WRITE;
/*!40000 ALTER TABLE `status_effects` DISABLE KEYS */;
INSERT INTO `status_effects` VALUES
(1,'Attack Up','buff','⚔️🔼','2025-03-31 07:40:47',0,0),
(2,'Defense Down','debuff','🛡️🔽','2025-03-31 07:40:47',0,0),
(3,'Poisoned','debuff','☣️','2025-03-31 07:40:47',0,0),
(4,'Regen','buff','❤️🔄','2025-03-31 07:40:47',0,0),
(5,'Stun','debuff','🌀','2025-03-31 07:40:47',0,0),
(6,'Burn','debuff','🔥','2025-03-31 07:40:47',0,0),
(7,'Freeze','debuff','❄️','2025-03-31 07:40:47',0,0),
(8,'Bio','debuff','☣️','2025-05-23 05:10:16',0,0),
(9,'Silence','debuff',NULL,'2025-05-25 02:24:50',0,0),
(10,'Evasion Up','buff',NULL,'2025-05-25 02:25:42',0,0),
(11,'Blind','debuff',NULL,'2025-05-25 02:25:42',0,0),
(12,'Defense Up','buff','🛡️🔼','2025-05-25 02:28:44',0,0),
(13,'Mag.Def Up','buff','🔮🛡️🔼','2025-05-25 02:28:44',0,0),
(14,'Mag.Def Down','debuff','🔮🛡️🔽','2025-05-25 02:33:23',0,0),
(15,'Berserk','neutral',NULL,'2025-05-25 02:34:39',0,0),
(16,'Magic Up','buff','🔮🔼','2025-05-25 02:36:05',0,0),
(17,'Haste','buff','⏱️🔼','2025-05-25 07:36:06',0,0),
(18,'Slow','debuff','⏳🔽','2025-05-25 07:36:07',0,0);
/*!40000 ALTER TABLE `status_effects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `temporary_abilities`
--

DROP TABLE IF EXISTS `temporary_abilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `temporary_abilities` (
  `temp_ability_id` int(11) NOT NULL AUTO_INCREMENT,
  `class_id` int(11) NOT NULL,
  `ability_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `effect` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`effect`)),
  `cooldown_turns` int(11) DEFAULT 0,
  `duration_turns` int(11) DEFAULT 1,
  `target_type` enum('self','enemy','ally','any') DEFAULT 'self',
  `icon_url` varchar(255) DEFAULT NULL,
  `element_id` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`temp_ability_id`),
  KEY `class_id` (`class_id`),
  KEY `element_id` (`element_id`),
  CONSTRAINT `temporary_abilities_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`class_id`) ON DELETE CASCADE,
  CONSTRAINT `temporary_abilities_ibfk_2` FOREIGN KEY (`element_id`) REFERENCES `elements` (`element_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `temporary_abilities`
--

LOCK TABLES `temporary_abilities` WRITE;
/*!40000 ALTER TABLE `temporary_abilities` DISABLE KEYS */;
INSERT INTO `temporary_abilities` VALUES
(1,1,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00'),
(2,2,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00'),
(3,3,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00'),
(4,4,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00'),
(5,5,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00'),
(6,6,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00'),
(7,7,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00'),
(8,8,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00'),
(9,9,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00'),
(10,10,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00'),
(11,11,'Pray','Heals you for 50% of your current HP.','{\"heal_current_pct\": 0.5}',3,5,'self',NULL,NULL,'2025-06-21 23:00:00');
/*!40000 ALTER TABLE `temporary_abilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trance_abilities`
--

DROP TABLE IF EXISTS `trance_abilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `trance_abilities` (
  `trance_id` int(11) NOT NULL,
  `ability_id` int(11) NOT NULL,
  KEY `trance_id` (`trance_id`),
  KEY `ability_id` (`ability_id`),
  CONSTRAINT `trance_abilities_ibfk_1` FOREIGN KEY (`trance_id`) REFERENCES `class_trances` (`trance_id`),
  CONSTRAINT `trance_abilities_ibfk_2` FOREIGN KEY (`ability_id`) REFERENCES `abilities` (`ability_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trance_abilities`
--

LOCK TABLES `trance_abilities` WRITE;
/*!40000 ALTER TABLE `trance_abilities` DISABLE KEYS */;
INSERT INTO `trance_abilities` VALUES
(1,54),
(1,55),
(1,56),
(1,57),
(2,58),
(2,59),
(2,60),
(2,61),
(3,74),
(3,75),
(3,76),
(3,77),
(4,62),
(4,63),
(4,64),
(4,65),
(5,78),
(5,79),
(5,80),
(5,81),
(6,66),
(6,67),
(6,68),
(6,69),
(7,56),
(7,61),
(7,69),
(7,53),
(8,82),
(8,85),
(8,87),
(9,83),
(9,84),
(9,86),
(10,70),
(10,71),
(10,72),
(10,73),
(11,79),
(12,204),
(12,205),
(12,206);
/*!40000 ALTER TABLE `trance_abilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `treasure_chest_instances`
--

DROP TABLE IF EXISTS `treasure_chest_instances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `treasure_chest_instances` (
  `instance_id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` int(11) NOT NULL,
  `room_id` int(11) NOT NULL,
  `chest_id` int(11) NOT NULL,
  `floor_id` int(11) NOT NULL,
  `coord_x` int(11) NOT NULL,
  `coord_y` int(11) NOT NULL,
  `step` int(11) NOT NULL DEFAULT 1,
  `correct_count` int(11) NOT NULL DEFAULT 0,
  `wrong_count` int(11) NOT NULL DEFAULT 0,
  `target_number` int(11) NOT NULL,
  `hint_value` int(11) NOT NULL,
  `is_unlocked` tinyint(1) NOT NULL DEFAULT 0,
  `is_broken` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`instance_id`),
  KEY `session_id` (`session_id`),
  KEY `room_id` (`room_id`),
  KEY `chest_id` (`chest_id`),
  KEY `floor_id` (`floor_id`),
  CONSTRAINT `treasure_chest_instances_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE,
  CONSTRAINT `treasure_chest_instances_ibfk_2` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`room_id`) ON DELETE CASCADE,
  CONSTRAINT `treasure_chest_instances_ibfk_3` FOREIGN KEY (`chest_id`) REFERENCES `treasure_chests` (`chest_id`) ON DELETE CASCADE,
  CONSTRAINT `treasure_chest_instances_ibfk_4` FOREIGN KEY (`floor_id`) REFERENCES `floors` (`floor_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `treasure_chest_instances`
--

LOCK TABLES `treasure_chest_instances` WRITE;
/*!40000 ALTER TABLE `treasure_chest_instances` DISABLE KEYS */;
INSERT INTO `treasure_chest_instances` VALUES
(1,2,71,1,1,0,7,1,0,0,12,5,0,0,'2025-12-21 01:14:04','2025-12-21 01:14:04');
/*!40000 ALTER TABLE `treasure_chest_instances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `treasure_chests`
--

DROP TABLE IF EXISTS `treasure_chests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `treasure_chests` (
  `chest_id` int(11) NOT NULL AUTO_INCREMENT,
  `chest_name` varchar(100) NOT NULL,
  `spawn_weight` float NOT NULL,
  `template_id` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`chest_id`),
  KEY `template_id` (`template_id`),
  CONSTRAINT `treasure_chests_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `room_templates` (`template_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `treasure_chests`
--

LOCK TABLES `treasure_chests` WRITE;
/*!40000 ALTER TABLE `treasure_chests` DISABLE KEYS */;
INSERT INTO `treasure_chests` VALUES
(1,'Gold Chest',1,12,'2025-04-25 08:22:25'),
(2,'Bronze Chest',1,12,'2025-04-25 18:47:46'),
(3,'Silver Chest',2,12,'2025-05-10 00:03:00');
/*!40000 ALTER TABLE `treasure_chests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'adventure'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-20 19:53:54
