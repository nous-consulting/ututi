alter table users add column openid varchar(200) default null unique;
alter table users add column facebook_id bigint default null unique;
