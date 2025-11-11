-- In dbt, you can combine SQL with Jinja, a templating language ('control structure')

-- Using Jinja turns your dbt project into a programming environment for SQL, 
-- giving you the ability to do things that aren't normally possible in SQL. 
-- It's important to note that Jinja itself isn't a programming language; 
-- instead, it acts as a tool to enhance and extend the capabilities of SQL within your dbt projects.
{% set film_title = "Dunkirk" %}

SELECT *
FROM {{ ref('films') }}
WHERE title = '{{ film_title }}'