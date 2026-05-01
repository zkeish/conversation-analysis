with cte_group_issues as (
  select distinct
      date(issue_start_dtt) as issue_date
    , issue_type
    , priority
    , cast(count(*) over (partition by issue_type, priority, date(issue_start_dtt)) as double) as issue_count
  from gold.dim_cx_issue i
  left join gold.dim_cx_metadata m
    on i.conversation_key = m.conversation_key
)
, cte_severity as (
  select distinct
      date(issue_start_dtt) as issue_date
    , issue_type
    , cast(count(*) over (partition by issue_type, date(issue_start_dtt)) as double) as severity_count
  from gold.dim_cx_issue i
  left join gold.dim_cx_metadata m
    on i.conversation_key = m.conversation_key
  where priority = 'high'
)
, cte_yesterdays_issues as (
  select
      *
    , lag(issue_count) over (partition by issue_type order by issue_date) as yesterdays_count
  from cte_group_issues
)
, cte_avg_count as (
  select
      issue_type
    , avg(issue_count) as average_2_day
  from cte_group_issues
  where issue_date between '2026-02-24' and '2026-02-25'
  group by issue_type
)
, cte_percentage_change as (
  select
    y.*
  , round(divide((y.issue_count - y.yesterdays_count), y.yesterdays_count), 2) day_over_day_change
  , round(divide((y.issue_count - a.average_2_day), a.average_2_day), 2) baseline_change
  from cte_yesterdays_issues y
  left join cte_avg_count a
  on y.issue_type = a.issue_type
  where yesterdays_count
)
, cte_spikes as (
select
    pc.*
  , case when day_over_day_change >= .5 
          then true else false end as spike_from_yesterday
  , case when baseline_change >= .5 
          then true else false end as spike_from_baseline
  from cte_percentage_change pc
  order by issue_date, issue_count
)
select
*
from cte_spikes
where 1=1
and (spike_from_baseline
or spike_from_yesterday)