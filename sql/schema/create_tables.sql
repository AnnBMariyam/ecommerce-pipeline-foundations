-- Stores customers who place orders
CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Stores products available for purchase
CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT products_unit_price_nonnegative
        CHECK (unit_price >= 0)
);

-- Stores one row for each customer order
CREATE TABLE IF NOT EXISTS orders (
    order_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    order_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT orders_customer_fk
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT orders_status_valid
        CHECK (
            status IN (
                'pending',
                'paid',
                'shipped',
                'cancelled',
                'refunded'
            )
        )
);



-- Stores the individual products contained in each order
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,

    CONSTRAINT order_items_order_fk
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
        ON DELETE CASCADE,

    CONSTRAINT order_items_product_fk
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT order_items_quantity_positive
        CHECK (quantity > 0),

    CONSTRAINT order_items_unit_price_nonnegative
        CHECK (unit_price >= 0)
);


-- Stores the last successfully processed position for each pipeline
CREATE TABLE IF NOT EXISTS pipeline_watermark (
    pipeline_name VARCHAR(100) PRIMARY KEY,
    last_processed_at TIMESTAMPTZ,
    last_processed_id BIGINT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);