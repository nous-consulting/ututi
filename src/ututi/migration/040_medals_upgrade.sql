create table user_medals (
       id bigserial not null,
       user_id int8 default null references users(id),
       medal_type varchar(30) not null,
       primary key (id));;

insert into user_medals (user_id, medal_type) values (1, 'admin2');
