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
    hash(conversation_id, primary_issue, secondary_issue) as issue_key
  , hash(conversation_id) as conversation_key
  , cast(primary_issue as varchar) as primary_issue
  , cast(secondary_issue as varchar) as secondary_issue
  , cast(issue_resolved as boolean) as issue_resolved
  , cast(resolution_type as varchar) as resolution_type
  , cast(resolution_notes as varchar) as resolution_notes
  , cast(issue_start_dtt as timestamp) as issue_start_dtt
  , cast(issue_resolved_dtt as timestamp) as issue_resolved_dtt
from cte_explode