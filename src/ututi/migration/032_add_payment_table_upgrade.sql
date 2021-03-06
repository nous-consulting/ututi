create table payments (
       id bigserial not null,
       group_id int8 default null references groups(id),
       user_id int8 default null references users(id),
       payment_type varchar(30),
       amount int8 default 0,
       valid bool default False,
       processed bool default False,
       created timestamp not null default (now() at time zone 'UTC'),
       referrer text,
       query_string text,

       raw_orderid varchar(250),
       raw_merchantid varchar(250),
       raw_lang varchar(250),
       raw_amount varchar(250),
       raw_currency varchar(250),
       raw_paytext varchar(250),
       raw__ss2 varchar(250),
       raw__ss1 varchar(250),
       raw_transaction2 varchar(250),
       raw_transaction varchar(250),
       raw_payment varchar(250),
       raw_name varchar(250),
       raw_surename varchar(250),
       raw_status varchar(250),
       raw_error varchar(250),
       raw_test varchar(250),
       raw_user varchar(250),
       raw_payent_type varchar(250),

       primary key (id));
