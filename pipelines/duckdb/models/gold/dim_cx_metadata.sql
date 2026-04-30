with cte_normalize as (
  select
      hash(conversation_id) as conversation_key
    , conversation_id
    , customer_id
    , metadata.category as category
    , metadata.issue_type as issue_type
    , metadata.product as product
    , metadata.status as status
    , metadata.priority as priority
    , metadata.created_at as conversation_first_message_dtt
    , metadata.updated_at as conversation_last_message_dtt
    , metadata.day as day
    , case when metadata.has_curveball then true else false end as has_curveball
    , case when metadata.spans_multiple_days then true else false end as spans_multiple_days
    , case when metadata.is_multi_issue then true else false end as is_multi_issue
    , case when metadata.is_long_conversation then true else false end as is_long_conversation
  from {{ ref('s_cx_convo_scd1') }}
)
select
    conversation_key as conversation_key
  , hash(customer_id) as customer_key
  , cast(conversation_id as varchar) as conversation_id
  , cast(customer_id as varchar) as customer_id
  , cast(category as varchar) as category
  , cast(issue_type as varchar) as issue_type
  , cast(product as varchar) as product
  , cast(status as varchar) as status
  , cast(priority as varchar) as priority
  , cast(conversation_first_message_dtt as timestamp) as conversation_first_message_dtt
  , cast(conversation_last_message_dtt as timestamp) as conversation_last_message_dtt
  , cast(day as varchar) as day
  , cast(has_curveball as boolean) as has_curveball
  , cast(spans_multiple_days as boolean) as spans_multiple_days
  , cast(is_multi_issue as boolean) as is_multi_issue
  , cast(is_long_conversation as boolean) as is_long_conversation
from cte_normalize