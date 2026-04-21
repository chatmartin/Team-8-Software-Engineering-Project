-- Ctrl+Eat production-ish MVP schema for Supabase/PostgreSQL.
-- Run this after rotating the previously committed credentials.

CREATE TABLE IF NOT EXISTS login_info (
  user_id BIGSERIAL PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  email_address TEXT UNIQUE,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE login_info
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user';

DO $$
BEGIN
  ALTER TABLE login_info
    ADD CONSTRAINT login_info_role_check CHECK (role IN ('user', 'admin'));
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS user_bio_data (
  user_id BIGINT PRIMARY KEY REFERENCES login_info(user_id) ON DELETE CASCADE,
  gender TEXT,
  height NUMERIC,
  weight NUMERIC,
  body_fat NUMERIC,
  age INTEGER,
  activity_level TEXT
);

CREATE TABLE IF NOT EXISTS nutrients (
  nutrient_id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  unit TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingredients (
  ingredient_id BIGSERIAL PRIMARY KEY,
  ingredient TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dietary_restrictions (
  restriction_id BIGSERIAL PRIMARY KEY,
  restriction TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user_restrictions (
  user_id BIGINT NOT NULL REFERENCES login_info(user_id) ON DELETE CASCADE,
  restriction_id BIGINT NOT NULL REFERENCES dietary_restrictions(restriction_id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, restriction_id)
);

CREATE TABLE IF NOT EXISTS user_allergies (
  user_id BIGINT NOT NULL REFERENCES login_info(user_id) ON DELETE CASCADE,
  allergen_id BIGINT NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
  severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
  PRIMARY KEY (user_id, allergen_id)
);

CREATE TABLE IF NOT EXISTS meals (
  meal_id BIGSERIAL PRIMARY KEY,
  meal TEXT NOT NULL,
  recipe_id BIGINT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS meal_nutrients (
  meal_id BIGINT NOT NULL REFERENCES meals(meal_id) ON DELETE CASCADE,
  nutrient_id BIGINT NOT NULL REFERENCES nutrients(nutrient_id) ON DELETE CASCADE,
  amount NUMERIC NOT NULL,
  PRIMARY KEY (meal_id, nutrient_id)
);

CREATE TABLE IF NOT EXISTS meal_ingredients (
  meal_id BIGINT NOT NULL REFERENCES meals(meal_id) ON DELETE CASCADE,
  ingredient_id BIGINT NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
  amount NUMERIC,
  unit TEXT,
  PRIMARY KEY (meal_id, ingredient_id)
);

CREATE TABLE IF NOT EXISTS queries (
  query_id BIGSERIAL PRIMARY KEY,
  query_signature TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS meal_queries (
  meal_id BIGINT NOT NULL REFERENCES meals(meal_id) ON DELETE CASCADE,
  query_id BIGINT NOT NULL REFERENCES queries(query_id) ON DELETE CASCADE,
  rank INTEGER NOT NULL,
  PRIMARY KEY (meal_id, query_id)
);

CREATE TABLE IF NOT EXISTS user_meals (
  user_meal_id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES login_info(user_id) ON DELETE CASCADE,
  meal_id BIGINT NOT NULL REFERENCES meals(meal_id) ON DELETE CASCADE,
  eaten_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_goals (
  user_id BIGINT NOT NULL REFERENCES login_info(user_id) ON DELETE CASCADE,
  nutrient_id BIGINT NOT NULL REFERENCES nutrients(nutrient_id) ON DELETE CASCADE,
  target_amount NUMERIC NOT NULL,
  min_max TEXT NOT NULL CHECK (min_max IN ('min', 'max')),
  PRIMARY KEY (user_id, nutrient_id)
);

CREATE TABLE IF NOT EXISTS recommendation_feedback (
  feedback_id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES login_info(user_id) ON DELETE CASCADE,
  meal_id BIGINT NOT NULL REFERENCES meals(meal_id) ON DELETE CASCADE,
  action TEXT NOT NULL CHECK (action IN ('saved', 'dismissed', 'logged', 'disliked')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO dietary_restrictions(restriction) VALUES
  ('glutenFree'), ('ketogenic'), ('vegetarian'), ('vegan'), ('pescetarian'),
  ('paleo'), ('primal'), ('whole30'), ('halal'), ('kosher'),
  ('beef free'), ('dairy free'), ('egg free')
ON CONFLICT DO NOTHING;

INSERT INTO nutrients(name, unit) VALUES
  ('calories', 'kcal'), ('protein', 'g'), ('fat', 'g'), ('carbohydrates', 'g'),
  ('saturated fat', 'g'), ('sugar', 'g'), ('fiber', 'g'), ('sodium', 'mg'),
  ('cholesterol', 'mg'), ('calcium', 'g'), ('iron', 'mg'), ('potassium', 'mg'),
  ('vitamin a', 'ug'), ('vitamin c', 'mg'), ('vitamin d', 'ug'),
  ('vitamin e', 'mg'), ('vitamin k', 'ug'), ('vitamin b1', 'mg'),
  ('vitamin b2', 'mg'), ('vitamin b3', 'mg'), ('vitamin b5', 'mg'),
  ('vitamin b6', 'mg'), ('vitamin b12', 'ug'), ('folate', 'ug'),
  ('magnesium', 'mg'), ('zinc', 'mg'), ('copper', 'mg'), ('manganese', 'mg'),
  ('phosphorus', 'mg'), ('selenium', 'ug'), ('iodine', 'ug'), ('choline', 'mg'),
  ('alcohol', 'g')
ON CONFLICT DO NOTHING;
