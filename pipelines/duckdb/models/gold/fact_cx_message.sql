with cte_explode as (
  select
      unnest(messages) as messages
    , conversation_id
    , customer_id
  from {{ ref('s_cx_convo_scd1') }}
)
select 
    messages.message_id as message_id
  , conversation_id
  , case when messages.role = 'agent' then 'bot_99999999' else customer_id end as sender_id
  , case when messages.role = 'customer' then 'bot_99999999' else customer_id end as receiver_id
  , messages.role as sender_role
  , messages.text as message_text
  , messages.created_at as message_sent_dtt
from cte_explode