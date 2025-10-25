-- Sample Requests Table for PostgreSQL
-- Tracks sample requests with product popularity metrics

CREATE TABLE IF NOT EXISTS sample_requests (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Product Information
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_code VARCHAR(100) NOT NULL,

    -- Requester Information
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,

    -- Request Details
    request_qty INTEGER,
    request_message TEXT,

    -- Status Management
    status VARCHAR(20) DEFAULT 'pending',
    -- Status values: pending, processing, approved, shipped, completed, cancelled

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    shipped_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Shipping Information (for future use)
    shipping_address TEXT,
    shipping_zipcode VARCHAR(10),
    tracking_number VARCHAR(100),

    -- Payment Information (for future use)
    payment_status VARCHAR(20), -- unpaid, paid, refunded
    payment_method VARCHAR(50),
    payment_amount DECIMAL(10, 2),
    payment_transaction_id VARCHAR(100),

    -- Admin Notes
    admin_notes TEXT,

    -- Indexes for product_id (for counting popular products)
    CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sample_requests_product_id ON sample_requests(product_id);
CREATE INDEX IF NOT EXISTS idx_sample_requests_status ON sample_requests(status);
CREATE INDEX IF NOT EXISTS idx_sample_requests_created_at ON sample_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sample_requests_company ON sample_requests(company_name);
CREATE INDEX IF NOT EXISTS idx_sample_requests_email ON sample_requests(contact_email);

-- Create view for product popularity (sample request count)
CREATE OR REPLACE VIEW product_sample_request_stats AS
SELECT
    product_id,
    product_name,
    product_code,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_requests,
    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_requests,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_requests,
    MAX(created_at) as last_requested_at
FROM sample_requests
GROUP BY product_id, product_name, product_code
ORDER BY total_requests DESC;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_sample_requests_updated_at BEFORE UPDATE
    ON sample_requests FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comment on table
COMMENT ON TABLE sample_requests IS 'Stores sample product requests from customers with status tracking';
COMMENT ON COLUMN sample_requests.product_id IS 'Reference to product idx';
COMMENT ON COLUMN sample_requests.status IS 'Request status: pending, processing, approved, shipped, completed, cancelled';
COMMENT ON VIEW product_sample_request_stats IS 'Aggregated statistics of sample requests per product for recommendation priority';
