const backend = process.env.ROUTER_API_URL || "http://127.0.0.1:8000";
export default {
  async rewrites() { return [{source: "/api/search", destination: backend + "/v1/search"}]; }
};
