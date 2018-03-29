/**
 * Clean up first.
 */
drop table if exists burgers;
drop table if exists restaurants;
drop table if exists restaurant_burgers;

/**
 * Burger information.
 */
create table burgers (
  id serial primary key,
  name text not null,
  quote text not null,
  ingredients text not null,
  url_suffix text not null
);

/**
 * Restaurant information.
 */
create table restaurants (
  id serial primary key,
  name text not null,
  phone_number text,
  -- Two JSON lists.
  address text not null,
  hours_of_operation text not null,
  -- JSON matrix of hours of operation.
  hours_table text,
  latitude real not null,
  longitude real not null,
  website text
);

/**
 * Table to associate burgers with restaurants; this way, we can keep them
 * separate and link multiple if need be.
 */
create table restaurant_burgers (
  id serial primary key,
  burger_id integer not null,
  restaurant_id integer not null
);
