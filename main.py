# Your name: Kishan Sripada
# Your student id: 5212 0336
# Your email: ksripada@umich.edu
# List who you have worked with on this project:

import unittest
import sqlite3
import json
import os


def read_data(filename):
  full_path = os.path.join(os.path.dirname(__file__), filename)
  f = open(full_path)
  file_data = f.read()
  f.close()
  json_data = json.loads(file_data)
  return json_data


def open_database(db_name):
  path = os.path.dirname(os.path.abspath(__file__))
  conn = sqlite3.connect(path + '/' + db_name)
  cur = conn.cursor()
  return cur, conn


def make_positions_table(data, cur, conn):
  positions = []
  for player in data['squad']:
    position = player['position']
    if position not in positions:
      positions.append(position)
  cur.execute(
    "CREATE TABLE IF NOT EXISTS Positions (id INTEGER PRIMARY KEY, position TEXT UNIQUE)"
  )
  for i in range(len(positions)):
    cur.execute("INSERT OR IGNORE INTO Positions (id, position) VALUES (?,?)",
                (i, positions[i]))
  conn.commit()


## [TASK 1]: 25 points
# Finish the function make_players_table

#     This function takes 3 arguments: JSON data,
#         the database cursor, and the database connection object


#     It iterates through the JSON data to get a list of players in the squad
#     and loads them into a database table called 'Players'
#     with the following columns:
#         id ((datatype: int; Primary key) - note this comes from the JSON
#         name (datatype: text)
#         position_id (datatype: integer)
#         birthyear (datatype: int)
#         nationality (datatype: text)
#     To find the position_id for each player, you will have to look up
#     the position in the Positions table we
#     created for you -- see make_positions_table above for details.
def make_players_table(data, cur, conn):
  cur.execute(
    "create table if not exists Players (id integer PRIMARY KEY, name TEXT, position_id INTEGER, birthyear INTEGER, nationality TEXT)"
  )

  for player in data['squad']:
    cur.execute("SELECT id FROM Positions WHERE position=?",
                (player['position'], ))
    position_id_result = cur.fetchone()
    if position_id_result:
      position_id = position_id_result[0]
    else:
      position_id = None

    birth_year = player['dateOfBirth'].split('-')[0]
    birth_year = int(birth_year)
    cur.execute(
      "insert or ignore into Players (id, name, position_id, birthyear, nationality) VALUES (?,?,?,?,?)",
      (player['id'], player['name'], position_id, birth_year,
       player['nationality']))
  conn.commit()


# [EXTRA CREDIT]
# You’ll make 3 new functions, make_winners_table(), make_seasons_table(),
# and winners_since_search(),
# and then write at least 2 meaningful test cases for each of them.

#     The first function takes 3 arguments: JSON data,
#     the database cursor, and the database connection object.
#     It makes a table with 2 columns:
#         id (datatype: int; Primary key) -- note this comes from the JSON
#         name (datatype: text) -- note: use the full, not short, name
#     hint: look at how we made the Positions table above for an example

#     The second function takes the same 3 arguments: JSON data,
#     the database cursor, and the database connection object.
#     It iterates through the JSON data to get info
#     about previous Premier League seasons (don't include the current one)
#     and loads all of the seasons into a database table
#     called ‘Seasons' with the following columns:
#         id (datatype: int; Primary key) - note this comes from the JSON
#         winner_id (datatype: text)
#         end_year (datatype: int)
#     NOTE: Skip seasons with no winner!

#     To find the winner_id for each season, you will have to
#     look up the winner's name in the Winners table
#     see make_winners_table above for details

#     The third function takes in a year (string), the database cursor,
#     and the database connection object. It returns a dictionary of how many
#     times each team has won the Premier League since the passed year.
#     In the dict, each winning team's (full) name is a key,
#     and the value associated with each team is the number of times
#     they have won since the year passed, including the season that ended
#     the passed year.


def make_winners_table(data, cur, conn):
  cur.execute(
    "create table if not exists Winners (id INTEGER PRIMARY KEY, name TEXT UNIQUE)"
  )

  for season in data['seasons']:
    if season.get('winner') is not None:
      id = season['winner']['id']
      name = season['winner']['name']
      cur.execute("insert OR ignore INTO Winners (id, name) VALUES (?,?)",
                  (id, name))
  conn.commit()


def make_seasons_table(data, cur, conn):
  cur.execute(
    "CREATE TABLE IF NOT EXISTS Seasons (id INTEGER PRIMARY KEY, winner_id INTEGER, end_year INTEGER)"
  )

  for season in data['seasons']:
    if season.get('winner'):
      season_id = season['id']
      winner_id = season['winner']['id']
      end_year = int(season['endDate'][:4])
      cur.execute(
        "INSERT OR IGNORE INTO Seasons (id, winner_id, end_year) VALUES (?,?,?)",
        (season_id, winner_id, end_year))
  conn.commit()


def winners_since_search(year, cur, conn):
  cur.execute(
    "SELECT W.name, COUNT(*) AS total_wins FROM Seasons S INNER JOIN Winners W ON S.winner_id = W.id WHERE S.end_year >= ? GROUP BY W.name ORDER BY total_wins DESC",
    (int(year), ))
  winners = cur.fetchall()
  return {winner[0]: winner[1] for winner in winners}


class TestAllMethods(unittest.TestCase):

  def setUp(self):
    path = os.path.dirname(os.path.abspath(__file__))
    self.conn = sqlite3.connect(path + '/' + 'Football.db')
    self.cur = self.conn.cursor()
    self.conn2 = sqlite3.connect(path + '/' + 'Football_seasons.db')
    self.cur2 = self.conn2.cursor()

  def test_players_table(self):
    self.cur.execute('SELECT * from Players')
    players_list = self.cur.fetchall()

    self.assertEqual(len(players_list), 30)
    self.assertEqual(len(players_list[0]), 5)
    self.assertIs(type(players_list[0][0]), int)
    self.assertIs(type(players_list[0][1]), str)
    self.assertIs(type(players_list[0][2]), int)
    self.assertIs(type(players_list[0][3]), int)
    self.assertIs(type(players_list[0][4]), str)

  def test_nationality_search(self):
    x = sorted(nationality_search(['England'], self.cur, self.conn))
    self.assertEqual(len(x), 11)
    self.assertEqual(len(x[0]), 3)
    self.assertEqual(x[0][0], "Aaron Wan-Bissaka")

    y = sorted(nationality_search(['Brazil'], self.cur, self.conn))
    self.assertEqual(len(y), 3)
    self.assertEqual(y[2], ('Fred', 2, 'Brazil'))
    self.assertEqual(y[0][1], 3)

  def test_birthyear_nationality_search(self):

    a = birthyear_nationality_search(24, 'England', self.cur, self.conn)
    self.assertEqual(len(a), 7)
    self.assertEqual(a[0][1], 'England')
    self.assertEqual(a[3][2], 1992)
    self.assertEqual(len(a[1]), 3)

  def test_type_speed_defense_search(self):
    b = sorted(position_birth_search('Goalkeeper', 35, self.cur, self.conn))
    self.assertEqual(len(b), 2)
    self.assertEqual(type(b[0][0]), str)
    self.assertEqual(type(b[1][1]), str)
    self.assertEqual(len(b[1]), 3)
    self.assertEqual(b[1], ('Jack Butland', 'Goalkeeper', 1993))

    c = sorted(position_birth_search("Defence", 23, self.cur, self.conn))
    self.assertEqual(len(c), 1)
    self.assertEqual(c, [('Teden Mengi', 'Defence', 2002)])

  def test_make_winners_table(self):
    self.cur2.execute('SELECT * FROM Winners')
    winners_list = self.cur2.fetchall()

    self.assertEqual(len(winners_list[0]), 2)
    self.assertIs(type(winners_list[0][1]), str)

  def test_make_seasons_table(self):
    self.cur2.execute('SELECT * FROM Seasons')
    seasons_list = self.cur2.fetchall()

    self.assertEqual(len(seasons_list[0]), 3)
    self.assertIs(type(seasons_list[0][0]), int)

  def test_winners_since_search(self):
    winners = winners_since_search("2021", self.cur2, self.conn2)
    self.assertEqual(winners, {"Manchester City FC": 1})

    winners = winners_since_search("2025", self.cur2, self.conn2)
    self.assertEqual(winners, {})


def main():

  # test_winners_since_search()
  # test_make_seasons_table()
  json_data = read_data('football.json')
  cur, conn = open_database('Football.db')
  make_positions_table(json_data, cur, conn)
  make_players_table(json_data, cur, conn)
  conn.close()

  seasons_json_data = read_data('football_PL.json')
  cur2, conn2 = open_database('Football_seasons.db')
  make_winners_table(seasons_json_data, cur2, conn2)
  make_seasons_table(seasons_json_data, cur2, conn2)
  conn2.close()


if __name__ == "__main__":
  main()
  unittest.main(verbosity=2)
