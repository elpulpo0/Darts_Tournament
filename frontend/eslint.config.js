import pluginVue from 'eslint-plugin-vue';
import tsPlugin from '@typescript-eslint/eslint-plugin';
const { configs: typescriptConfigs } = tsPlugin;
import parser from '@typescript-eslint/parser';
import prettier from 'eslint-config-prettier';
import vueParser from 'vue-eslint-parser';

export default [
    {
        ignores: [
            '**/*.json',
            '**/*.html',
            'package-lock.json',
            'tsconfig.json',
            'jsconfig.json',
            'build-meta.json',
        ],
    },
    // JavaScript et TypeScript
    {
        files: ['**/*.{js,jsx,ts,tsx}'],
        languageOptions: {
            parser,
            parserOptions: {
                ecmaVersion: 'latest',
                sourceType: 'module',
            },
        },
        plugins: {
            '@typescript-eslint': typescriptConfigs,
        },
        rules: {
            'no-console': ['error', { allow: ['warn', 'error', 'info'] }],
            '@typescript-eslint/no-dynamic-delete': 'off',
        },
    },

    // Vue
    {
        files: ['**/*.vue'],
        languageOptions: {
            parser: vueParser,
            parserOptions: {
                parser,
                ecmaVersion: 'latest',
                sourceType: 'module',
            },
        },
        plugins: {
            vue: pluginVue,
        },
        rules: {
            ...pluginVue.configs['flat/recommended'].rules,
            'vue/attribute-hyphenation': ['error', 'never'],
            'vue/attributes-order': [
                'error',
                {
                    order: [
                        'DEFINITION',
                        'LIST_RENDERING',
                        'CONDITIONALS',
                        'RENDER_MODIFIERS',
                        'GLOBAL',
                        'SLOT',
                        'TWO_WAY_BINDING',
                        'OTHER_DIRECTIVES',
                        'OTHER_ATTR',
                        'EVENTS',
                        'CONTENT',
                        'UNIQUE',
                    ],
                    alphabetical: false,
                },
            ],
            'vue/first-attribute-linebreak': 'off',
            'vue/component-name-in-template-casing': ['error', 'PascalCase'],
            'vue/html-closing-bracket-newline': ['error', { singleline: 'never', multiline: 'never' }],
            'vue/max-attributes-per-line': [
                'error',
                {
                    singleline: 1,
                    multiline: 1,
                },
            ],
            'vue/no-multiple-template-root': 'off',
            'vue/no-mutating-props': ['error', { shallowOnly: true }],
            'vue/no-v-html': 'off',
            'vue/prop-name-casing': ['error', 'camelCase'],
        },
    },

    // Tests (TypeScript ou JS)
    {
        files: ['**/*.test.{js,ts}', '**/tests/**/*.{js,ts}'],
        rules: {
            '@typescript-eslint/no-explicit-any': 'off',
        },
    },

    // Prettier
    {
        files: ['**/*.{js,ts,vue,json,scss,html}'],
        rules: {
            ...prettier.rules,
        },
    },
];
