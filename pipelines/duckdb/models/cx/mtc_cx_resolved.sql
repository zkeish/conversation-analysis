{{ config(materialized='incremental', unique_key='conversation_key') }}

with cte_obt as (
select 
      fm.*
    , issue_resolved
    , issue_type
    , product as product_name
    , resolution_type
    , resolution_notes
from {{ ref('fact_cx_message') }} fm
left join {{ ref('dim_cx_metadata') }} dm
on fm.conversation_key = dm.conversation_key
left join {{ ref('dim_cx_issue') }} i
on fm.conversation_key = i.conversation_key
)
, cte_agg as (
select
  conversation_key
, issue_type
, product_name
, resolution_type
, resolution_notes
, string_agg(message_text, ' ') AS conversation_text
from cte_obt
where issue_resolved
group by 1,2,3,4,5
)
select
      a.*
    , coalesce(t.embedding, cast(null as float[768])) as embedding
from cte_agg a
left join {{ this }} t
  on a.conversation_key = t.conversation_key

{% if is_incremental() %}
where a.conversation_key not in (
    select conversation_key from {{ this }}
)
{% endif %}