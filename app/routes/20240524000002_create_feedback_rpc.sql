-- Create a function to aggregate feedback stats with optional date filtering
create or replace function get_clinic_feedback_stats(
    start_date timestamp with time zone default null,
    end_date timestamp with time zone default null
)
returns table (
    clinic_id uuid,
    clinic_name text,
    up bigint,
    down bigint,
    total bigint
)
language plpgsql
as $$
begin
    return query
    select
        f.clinic_id,
        c.clinic_name,
        count(*) filter (where f.rating = 'up') as up,
        count(*) filter (where f.rating = 'down') as down,
        count(*) as total
    from chat_feedback f
    left join clinics c on f.clinic_id = c.id
    where
        (start_date is null or f.created_at >= start_date)
        and (end_date is null or f.created_at <= end_date)
    group by f.clinic_id, c.clinic_name;
end;
$$;

-- Secure the function: Revoke from public, grant only to service_role
revoke execute on function get_clinic_feedback_stats(timestamp with time zone, timestamp with time zone) from public;
grant execute on function get_clinic_feedback_stats(timestamp with time zone, timestamp with time zone) to service_role;