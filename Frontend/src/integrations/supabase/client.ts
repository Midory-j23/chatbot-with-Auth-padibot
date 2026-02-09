// import pkg from "pg";
// const { Pool } = pkg;

// export const pool = new Pool({
//   user: "postgres",
//   host: "localhost",
//   database: "chatbot",
//   password: "YOUR_PASSWORD",
//   port: 5432,
// });


// TEMP MOCK – Supabase disabled
export const supabase = {
  auth: {
    signInWithPassword: async () => ({ data: null, error: null }),
    signUp: async () => ({ data: null, error: null }),
    signOut: async () => ({ error: null }),
    getUser: async () => ({ data: { user: null }, error: null }),
    onAuthStateChange: () => ({
      data: { subscription: { unsubscribe: () => {} } },
    }),
  },
}
