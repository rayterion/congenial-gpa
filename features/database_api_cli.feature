Feature: Can send database API requests and store values

  Background:
    Given the database API is running
    And the database is empty

  Scenario: Launch CLI
    When I run the database CLI
    Then it should launch a welcome page
    And it should contain a commands section
    And the commands section should include /add_cell
    And the commands section should include /get_cell
    And the commands section should include /update_cell
    And the commands section should include /remove_cell
    And the commands section should include /add_row
    And the commands section should include /get_row
    And the commands section should include /update_row
    And the commands section should include /remove_row
    And the commands section should include /list_rows
    And the commands section should include /clear_database
    And the commands section should include /help
    And the commands section should include /exit

  Scenario: Add a cell
    Given I have launched the database CLI
    When I run the command "/add_cell users 1 name Martin"
    Then the CLI should send a create cell request to the database API
    And the database should store "Martin" in table "users", row "1", cell "name"
    And the CLI should show a success message

  Scenario: Get a cell
    Given the database has table "users", row "1", cell "name" with value "Martin"
    And I have launched the database CLI
    When I run the command "/get_cell users 1 name"
    Then the CLI should send a read cell request to the database API
    And the CLI should show the value "Martin"

  Scenario: Update a cell
    Given the database has table "users", row "1", cell "name" with value "Martin"
    And I have launched the database CLI
    When I run the command "/update_cell users 1 name Tulio"
    Then the CLI should send an update cell request to the database API
    And the database should store "Tulio" in table "users", row "1", cell "name"
    And the CLI should show a success message

  Scenario: Remove a cell
    Given the database has table "users", row "1", cell "name" with value "Martin"
    And I have launched the database CLI
    When I run the command "/remove_cell users 1 name"
    Then the CLI should send a delete cell request to the database API
    And table "users", row "1" should not contain cell "name"
    And the CLI should show a success message

  Scenario: Add a row
    Given I have launched the database CLI
    When I run the command "/add_row users 1 name=Martin age=20 role=developer"
    Then the CLI should send a create row request to the database API
    And the database should store the following row in table "users":
      | id | name   | age | role      |
      | 1  | Martin | 20  | developer |
    And the CLI should show a success message

  Scenario: Get a row
    Given the database has the following row in table "users":
      | id | name   | age | role      |
      | 1  | Martin | 20  | developer |
    And I have launched the database CLI
    When I run the command "/get_row users 1"
    Then the CLI should send a read row request to the database API
    And the CLI should show the following row:
      | id | name   | age | role      |
      | 1  | Martin | 20  | developer |

  Scenario: Update a row
    Given the database has the following row in table "users":
      | id | name   | age | role      |
      | 1  | Martin | 20  | developer |
    And I have launched the database CLI
    When I run the command "/update_row users 1 name=Tulio age=21 role=engineer"
    Then the CLI should send an update row request to the database API
    And the database should store the following row in table "users":
      | id | name  | age | role     |
      | 1  | Tulio | 21  | engineer |
    And the CLI should show a success message

  Scenario: Remove a row
    Given the database has the following row in table "users":
      | id | name   | age | role      |
      | 1  | Martin | 20  | developer |
    And I have launched the database CLI
    When I run the command "/remove_row users 1"
    Then the CLI should send a delete row request to the database API
    And table "users" should not contain row "1"
    And the CLI should show a success message

  Scenario: List rows
    Given the database has the following rows in table "users":
      | id | name   | age | role      |
      | 1  | Martin | 20  | developer |
      | 2  | Ana    | 22  | designer  |
    And I have launched the database CLI
    When I run the command "/list_rows users"
    Then the CLI should send a list rows request to the database API
    And the CLI should show the following rows:
      | id | name   | age | role      |
      | 1  | Martin | 20  | developer |
      | 2  | Ana    | 22  | designer  |

  Scenario: Clear database
    Given the database has the following rows in table "users":
      | id | name   |
      | 1  | Martin |
      | 2  | Ana    |
    And I have launched the database CLI
    When I run the command "/clear_database"
    Then the CLI should send a clear database request to the database API
    And the database should be empty
    And the CLI should show a success message

  Scenario: Show help
    Given I have launched the database CLI
    When I run the command "/help"
    Then the CLI should show the commands section
    And the commands section should include all available database operations

  Scenario: Exit CLI
    Given I have launched the database CLI
    When I run the command "/exit"
    Then the CLI should close successfully

  Scenario: Show an error when command is unknown
    Given I have launched the database CLI
    When I run the command "/unknown_command"
    Then the CLI should show an unknown command error
    And the CLI should remain open

  Scenario: Show an error when required command arguments are missing
    Given I have launched the database CLI
    When I run the command "/add_cell users 1"
    Then the CLI should show a missing arguments error
    And the CLI should explain the correct command usage
    And the CLI should remain open

  Scenario: Show an error when getting a cell that does not exist
    Given I have launched the database CLI
    When I run the command "/get_cell users 1 name"
    Then the CLI should send a read cell request to the database API
    And the CLI should show a not found error

  Scenario: Show an error when getting a row that does not exist
    Given I have launched the database CLI
    When I run the command "/get_row users 1"
    Then the CLI should send a read row request to the database API
    And the CLI should show a not found error