alter table wall_posts add column group_id int8 references groups(id) on delete cascade default null;

create or replace function wall_post_event_trigger() returns trigger as $$
    begin
        if new.subject_id is not null then
            insert into events(object_id, author_id, event_type)
                   values (new.id, cast(current_setting('ututi.active_user') as int8), 'subject_wall_post');
        elsif new.location_id is not null then
            insert into events(object_id, author_id, event_type)
                   values (new.id, cast(current_setting('ututi.active_user') as int8), 'location_wall_post');
        end if;
        return new;
    end
$$ language plpgsql;

drop trigger after_wall_post_event_trigger on wall_posts;

create trigger group_wall_post_event_trigger after insert or update on wall_posts
    for each row execute procedure wall_post_event_trigger();
