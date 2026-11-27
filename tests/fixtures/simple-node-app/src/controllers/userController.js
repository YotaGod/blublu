const userService = require("../services/userService");

const getAllUsers = (req, res) => {
  const users = userService.findUsers();
  res.status(200).json({ success: true, data: users });
};

const getUserById = (req, res) => {
  const user = userService.findUserById(req.params.id);
  if (!user) {
    return res.status(404).json({ success: false, message: "User not found" });
  }
  res.status(200).json({ success: true, data: user });
};

const createUser = (req, res) => {
  const { name, email } = req.body;
  if (!name || !email) {
    return res.status(400).json({ success: false, message: "Name and email are required" });
  }
  const newUser = userService.registerUser({ name, email });
  res.status(201).json({ success: true, data: newUser });
};

module.exports = {
  getAllUsers,
  getUserById,
  createUser
};
