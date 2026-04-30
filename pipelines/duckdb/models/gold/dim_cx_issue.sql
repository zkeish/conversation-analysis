with cte_explode as (
select
      unnest(metadata.secondary_issues) as secondary_issue
    , metadata.issue_type as primary_issue
    , conversation_id
    , metadata.created_at as issue_start_dtt
    , resolution.resolved_at as issue_resolved_dtt
    , case when metadata.status = 'resolved' then true else false end as issue_resolved
    , resolution.resolution_type as resolution_type
    , resolution.resolution_notes as resolution_notes
from {{ ref('s_cx_convo_scd1') }}
)
select distinct
    md5(concat(conversation_id, primary_issue, secondary_issue)) as issue_id
  , conversation_id
  , primary_issue
  , secondary_issue
  , issue_resolved
  , resolution_type
  , resolution_notes
  , issue_start_dtt
  , issue_resolved_dtt
from cte_explode