{% macro generate_film_ratings() %}

WITH films_with_ratings AS ( --this is the first CTE, the sub-query/wrapper. maintainable, scoped script.
    SELECT
        film_id,
        title,
        release_date,
        price,
        rating,
        user_rating,
        {{ generate_ratings() }}
    FROM {{ ref('films') }}
),

films_with_actors AS ( --this is the second cte
    SELECT
        f.film_id,
        f.title,
        STRING_AGG(a.actor_name, ',') AS actors --is this doing anything? the string_agg? or would it only if we had more actors saved per move?
    FROM {{ ref('films') }} f
    LEFT JOIN {{ ref('film_actors') }} fa ON f.film_id = fa.film_id
    LEFT JOIN {{ ref('actors') }} a ON fa.actor_id = a.actor_id
    GROUP BY f.film_id, f.title
)

SELECT 
    fwr.*,
    fwa.actors
FROM films_with_ratings fwr 
LEFT JOIN films_with_actors fwa ON fwr.film_id = fwa.film_id

{% endmacro %}