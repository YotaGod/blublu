import { useState } from "react";

export function useAuth() {
  const [user, setUser] = useState({
    id: "usr_1",
    name: "Demo Developer",
    email: "dev@example.com"
  });

  const logout = () => {
    setUser(null);
  };

  return {
    user,
    logout
  };
}
