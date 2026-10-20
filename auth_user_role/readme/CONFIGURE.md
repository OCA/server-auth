To configure role mappings:

1. Navigate to **Settings > Users & Companies > Identity Role Mappings**.
2. Create a new mapping rule.
3. Define the **Identity Attribute**: Enter the exact payload attribute key provided by your IdP (e.g., `department`, `groups`, `eduPersonAffiliation`).
4. Select the **Operator**:
   * **equals**: The payload value must exactly match the defined value.
   * **contains**: The payload value must contain the defined value (useful for comma-separated lists or longer strings).
5. Define the **Value** you expect to receive from the IdP.
6. Select the **Role** (from `base_user_role`) that should be assigned when the condition is met.