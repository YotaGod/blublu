// In-memory data store for simple-node-app fixture
const users = [
  { id: "1", name: "Alice Smith", email: "alice@example.com" },
  { id: "2", name: "Bob Jones", email: "bob@example.com" }
];

const findUsers = () => {
  return [...users];
};

const findUserById = (id) => {
  return users.find((u) => u.id === id) || null;
};

const registerUser = ({ name, email }) => {
  const newUser = {
    id: String(users.length + 1),
    name,
    email
  };
  users.push(newUser);
  return newUser;
};

module.exports = {
  findUsers,
  findUserById,
  registerUser
};
