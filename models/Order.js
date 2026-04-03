const mongoose = require('mongoose');

const orderSchema = new mongoose.Schema(
  {
    // Dashboard fields (from manual "Add Order" form)
    orderNumber:  { type: String, required: true },
    merchant:     { type: String, required: true },
    amount:       { type: Number, required: true },
    purchaseDate: { type: Date, default: Date.now },
    status:       { type: String, default: 'delivered' },
    refundStatus: { type: String, default: 'none', enum: ['none', 'pending', 'approved', 'rejected'] },
    refundAmount: { type: Number, default: null },

    // Gmail parser fields
    gmailMessageId: { type: String, default: null },
    platform:       { type: String, default: null },
    emailType:      { type: String, default: null },
    orderId:        { type: String, default: null },
    productName:    { type: String, default: null },
    otp:            { type: String, default: null },
    deliveryDate:   { type: Date, default: null },
    returnDeadline: { type: Date, default: null },
    daysRemaining:  { type: Number, default: null },
    returnWindowDays: { type: Number, default: null },
    rawSnippet:     { type: String, default: null },

    // User association (for future multi-user support)
    userId: { type: String, default: 'default' },
  },
  { timestamps: true }
);

// Prevent duplicate Gmail messages
orderSchema.index({ gmailMessageId: 1 }, { unique: true, sparse: true });

module.exports = mongoose.model('Order', orderSchema);
