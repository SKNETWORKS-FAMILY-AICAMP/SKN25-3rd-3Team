CREATE TABLE parsed_recipe (
    id BIGSERIAL PRIMARY KEY,

    raw_recipe_id TEXT NOT NULL,
    source TEXT NOT NULL,
    source_recipe_id TEXT,

    title TEXT NOT NULL,
    url TEXT NOT NULL,

    category_name TEXT,
    category_param TEXT,
    category_id TEXT,

    parse_status TEXT NOT NULL DEFAULT 'parsed',
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (parse_status IN ('parsed', 'partial', 'failed')),
    UNIQUE (raw_recipe_id),
    UNIQUE (source, source_recipe_id)
);

CREATE TABLE parsed_recipe_step (
    id BIGSERIAL PRIMARY KEY,

    parsed_recipe_id BIGINT NOT NULL
        REFERENCES parsed_recipe(id) ON DELETE CASCADE,

    step_index INT NOT NULL,
    content TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (step_index >= 1),
    UNIQUE (parsed_recipe_id, step_index)
);

CREATE TABLE parsed_recipe_ingredient (
    id BIGSERIAL PRIMARY KEY,

    parsed_recipe_id BIGINT NOT NULL
        REFERENCES parsed_recipe(id) ON DELETE CASCADE,

    ingredient_index INT NOT NULL,

    raw_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,

    ingredient_name_raw TEXT,
    ingredient_name_raw_normalized TEXT,

    quantity_text TEXT,

    quantity_value DOUBLE PRECISION,
    quantity_min DOUBLE PRECISION,
    quantity_max DOUBLE PRECISION,

    quantity_unit_raw TEXT,
    quantity_unit_normalized TEXT,

    is_optional BOOLEAN NOT NULL DEFAULT FALSE,
    annotations JSONB NOT NULL DEFAULT '[]'::jsonb,

    entity_type TEXT NOT NULL,
    parse_status TEXT NOT NULL,

    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (entity_type IN ('ingredient', 'tool', 'unknown')),
    CHECK (parse_status IN ('parsed', 'partial', 'failed')),

    UNIQUE (parsed_recipe_id, ingredient_index)
);
