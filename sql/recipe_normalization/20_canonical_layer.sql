CREATE TABLE ingredient (
    id BIGSERIAL PRIMARY KEY,

    canonical_name TEXT NOT NULL,
    canonical_name_normalized TEXT NOT NULL,

    group_name TEXT,
    group_name_normalized TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (canonical_name_normalized)
);

CREATE TABLE ingredient_alias (
    id BIGSERIAL PRIMARY KEY,

    ingredient_id BIGINT NOT NULL
        REFERENCES ingredient(id) ON DELETE CASCADE,

    alias_name TEXT NOT NULL,
    alias_name_normalized TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (alias_name_normalized)
);
