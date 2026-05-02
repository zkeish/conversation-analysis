with cte_obt as (
select 
      fm.*
    , issue_resolved
    , issue_type
    , product as product_name
    , resolution_type
    , resolution_notes
    , row_number() over (partition by fm.conversation_key order by message_sent_dtt) as rn
from {{ ref('fact_cx_message') }} fm
left join {{ ref('dim_cx_metadata') }} dm
on fm.conversation_key = dm.conversation_key
left join {{ ref('dim_cx_issue') }} i
on fm.conversation_key = i.conversation_key
where sender_role = 'customer'
)
select
  conversation_key
, issue_type
, product_name
, message_text
, message_sent_dtt
from cte_obt
where not issue_resolved
and rn = 1
order by conversation_key