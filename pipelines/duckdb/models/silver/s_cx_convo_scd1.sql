{{ config(materialized='incremental', unique_key='conversation_id') }}
with cte_ranked as (

    select *,
           row_number() over (partition by conversation_id order by load_dtt desc) as rn
    from {{ ref('b_cx_convo') }}

    {% if is_incremental() %}
    where load_dtt > (select coalesce(max(load_dtt), '1900-01-01')
       from {{ this }})
    {% endif %}
)
select
      conversation_id
    , customer_id
    , messages
    , metadata
    , resolution
    , load_dtt
from cte_ranked
where rn = 1