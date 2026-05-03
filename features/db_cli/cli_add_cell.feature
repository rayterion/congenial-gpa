Feature: Database CLI - Add Cell
  As a user of the database CLI
  I want to be able to add a cell to a table
  So that I can store data in the database

Scenario: Add a cell
    When I run the command "db-cli /add_cell value=Martin row=followers column=name table=users --db_api_url=http://localhost:8000"
    Then the CLI should send a create cell request to the database API
    And the database should store "Martin" in table "users", row "followers", column "name"
    And the CLI should show a success message