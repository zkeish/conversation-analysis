with cte_explode as (
  select
      unnest(messages) as messages
    , conversation_id
    , customer_id
  from {{ ref('s_cx_convo_scd1') }}
)
, cte_clean_columns as (
select
    hash(messages.message_id) as message_key
  , messages.message_id as message_id
  , conversation_id
  , case when messages.role = 'agent' then 'bot_99999999' else customer_id end as sender_id
  , case when messages.role = 'customer' then 'bot_99999999' else customer_id end as receiver_id
  , hash(customer_id) as customer_key
  , messages.role as sender_role
  , messages.text as message_text
  , messages.created_at as message_sent_dtt
from cte_explode
)
select
    message_key as message_key
  , hash(conversation_id) as conversation_key
  , customer_key as customer_key
  , cast(message_id as varchar) as message_id
  , cast(sender_role as varchar) as sender_role
  , cast(message_text as varchar) as message_text
  , cast(message_sent_dtt as timestamp) as message_sent_dtt
from cte_clean_columns