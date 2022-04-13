--
-- Base de données : `gamebot`
--
CREATE DATABASE IF NOT EXISTS `gamebot` DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;
USE `gamebot`;

-- --------------------------------------------------------

--
-- Structure de la table `stats`
--

DROP TABLE IF EXISTS `stats`;
CREATE TABLE IF NOT EXISTS `stats` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `game_name` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `but_up` int(8) NOT NULL DEFAULT '0',
  `but_down` int(8) NOT NULL DEFAULT '0',
  `but_right` int(8) NOT NULL DEFAULT '0',
  `but_left` int(8) NOT NULL DEFAULT '0',
  `but_a` int(8) NOT NULL DEFAULT '0',
  `but_b` int(8) NOT NULL DEFAULT '0',
  `but_start` int(8) NOT NULL DEFAULT '0',
  `but_select` int(8) NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`),
  UNIQUE KEY `game_name` (`game_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Déchargement des données de la table `stats`
--

INSERT INTO `stats` (`ID`, `game_name`, `but_up`, `but_down`, `but_right`, `but_left`, `but_a`, `but_b`, `but_start`, `but_select`) VALUES
(1, 'Pokemon-Version_Rouge.gb', 0, 0, 0, 0, 0, 0, 0, 0);