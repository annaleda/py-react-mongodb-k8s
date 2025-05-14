import { useEffect, useState } from "react";

function App() {
  const [msg, setMsg] = useState("");

  useEffect(() => {
    fetch("/api/hello")
      .then(res => res.json())
      .then(data => setMsg(data.message))
      .catch(console.error);
  }, []);

  return (
    <div>
      <h1>React + Flask + Mongo + Nginx</h1>
      <p>Message: {msg}</p>
    </div>
  );
}

export default App;
