with cte_normalize as (
  select
      conversation_id
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
    , metadata.secondary_issues as secondary_issues
    , case when metadata.is_long_conversation then true else false end as is_long_conversation
  from {{ ref('s_cx_convo_scd1') }}
)
select 
  *
from cte_normalize