const mongoose = require('mongoose');

const userSchema = new mongoose.Schema(
  {
    googleId:     { type: String, required: true, unique: true },
    email:        { type: String, required: true },
    name:         { type: String, default: null },
    picture:      { type: String, default: null },
    accessToken:  { type: String, default: null },
    refreshToken: { type: String, default: null },
    tokenExpiry:  { type: Date, default: null },
  },
  { timestamps: true }
);

module.exports = mongoose.model('User', userSchema);
