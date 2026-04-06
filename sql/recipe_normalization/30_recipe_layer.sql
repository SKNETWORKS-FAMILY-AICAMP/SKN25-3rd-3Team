CREATE TABLE recipe (
    id BIGSERIAL PRIMARY KEY,

    parsed_recipe_id BIGINT NOT NULL
        REFERENCES parsed_recipe(id) ON DELETE RESTRICT,

    raw_recipe_id TEXT NOT NULL,
    source TEXT NOT NULL,
    source_recipe_id TEXT,

    title TEXT NOT NULL,
    url TEXT NOT NULL,

    category_name TEXT,
    category_id TEXT,

    canonical_status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (canonical_status IN ('active', 'draft', 'archived')),

    UNIQUE (parsed_recipe_id),
    UNIQUE (source, raw_recipe_id)
);

CREATE TABLE recipe_ingredient (
    id BIGSERIAL PRIMARY KEY,

    recipe_id BIGINT NOT NULL
        REFERENCES recipe(id) ON DELETE CASCADE,

    parsed_recipe_ingredient_id BIGINT
        REFERENCES parsed_recipe_ingredient(id) ON DELETE SET NULL,

    ingredient_index INT NOT NULL,

    ingredient_id BIGINT
        REFERENCES ingredient(id) ON DELETE RESTRICT,

    ingredient_name_raw_snapshot TEXT NOT NULL,

    normalization_status TEXT NOT NULL,

    quantity_text TEXT,
    quantity_value DOUBLE PRECISION,
    quantity_min DOUBLE PRECISION,
    quantity_max DOUBLE PRECISION,
    quantity_unit_normalized TEXT,

    is_optional BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (normalization_status IN ('matched', 'alias_matched', 'group_matched', 'unmatched')),

    CHECK (
        (normalization_status = 'unmatched' AND ingredient_id IS NULL) OR
        (normalization_status <> 'unmatched' AND ingredient_id IS NOT NULL)
    ),

    UNIQUE (recipe_id, ingredient_index)
);
