CREATE TABLE user_inventory (
    id BIGSERIAL PRIMARY KEY,

    user_id TEXT NOT NULL,

    ingredient_id BIGINT NOT NULL
        REFERENCES ingredient(id) ON DELETE RESTRICT,

    quantity_value DOUBLE PRECISION,
    quantity_unit_normalized TEXT,
    quantity_text TEXT,

    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (user_id, ingredient_id)
);
