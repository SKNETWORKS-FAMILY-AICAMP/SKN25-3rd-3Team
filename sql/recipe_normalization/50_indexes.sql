CREATE INDEX idx_recipe_title_trgm
    ON recipe
    USING GIN (lower(title) gin_trgm_ops);

CREATE INDEX idx_recipe_ingredient_ing
    ON recipe_ingredient (ingredient_id);

CREATE INDEX idx_parsed_ing_raw_norm
    ON parsed_recipe_ingredient (ingredient_name_raw_normalized);

CREATE INDEX idx_alias_norm
    ON ingredient_alias (alias_name_normalized);
