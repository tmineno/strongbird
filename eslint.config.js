export default [
    {
        files: ["**/*.js"],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: "module",
            globals: {
                console: "readonly",
                document: "readonly",
                window: "readonly",
                // MathJax global variables
                MathJax: "readonly",
            }
        },
        rules: {
            "no-unused-vars": "warn",
            "no-console": "off",
            "prefer-const": "error",
            "no-var": "error",
            "semi": ["error", "always"],
            "no-undef": "error",
            "no-redeclare": "error",
            "no-unreachable": "error"
        }
    }
];
