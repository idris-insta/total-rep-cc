import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';
import fs from 'fs';
import { execSync } from 'child_process';

// Read Supervisor code-server password from conf.d
function getCodeServerPassword() {
  try {
    const conf = fs.readFileSync(
      '/etc/supervisor/conf.d/supervisord_code_server.conf',
      'utf8'
    );
    const match = conf.match(/PASSWORD="([^"]+)"/);
    return match ? match[1] : null;
  } catch {
    return null;
  }
}

const SUP_PASS = getCodeServerPassword();

// Visual edits plugin for Vite
function visualEditsPlugin() {
  return {
    name: 'visual-edits',
    configureServer(server) {
      // CORS origin validation
      const isAllowedOrigin = (origin) => {
        if (!origin) return false;
        if (origin.match(/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/)) return true;
        if (origin.match(/^https:\/\/([a-zA-Z0-9-]+\.)*emergent\.sh$/)) return true;
        if (origin.match(/^https:\/\/([a-zA-Z0-9-]+\.)*emergentagent\.com$/)) return true;
        if (origin.match(/^https:\/\/([a-zA-Z0-9-]+\.)*appspot\.com$/)) return true;
        return false;
      };

      server.middlewares.use('/ping', (req, res) => {
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ status: 'ok', time: new Date().toISOString() }));
      });

      server.middlewares.use('/edit-file', async (req, res, next) => {
        if (req.method === 'OPTIONS') {
          const origin = req.headers.origin;
          if (origin && isAllowedOrigin(origin)) {
            res.setHeader('Access-Control-Allow-Origin', origin);
            res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
            res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-api-key');
            res.statusCode = 200;
            res.end();
          } else {
            res.statusCode = 403;
            res.end();
          }
          return;
        }

        if (req.method !== 'POST') {
          next();
          return;
        }

        const origin = req.headers.origin;
        if (origin && isAllowedOrigin(origin)) {
          res.setHeader('Access-Control-Allow-Origin', origin);
          res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-api-key');
        }

        const key = req.headers['x-api-key'];
        if (!SUP_PASS || key !== SUP_PASS) {
          res.statusCode = 401;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'Unauthorized' }));
          return;
        }

        let body = '';
        req.on('data', chunk => { body += chunk; });
        req.on('end', () => {
          try {
            const { changes } = JSON.parse(body);
            if (!changes || !Array.isArray(changes) || changes.length === 0) {
              res.statusCode = 400;
              res.setHeader('Content-Type', 'application/json');
              res.end(JSON.stringify({ error: 'No changes provided' }));
              return;
            }

            // Import AST processing libraries dynamically
            const parser = require('@babel/parser');
            const traverse = require('@babel/traverse').default;
            const generate = require('@babel/generator').default;
            const t = require('@babel/types');

            const frontendRoot = path.resolve(__dirname);
            const edits = [];
            const rejectedChanges = [];

            const getRelativePath = (absolutePath) => {
              const rel = path.relative(frontendRoot, absolutePath);
              return '/' + rel;
            };

            const findFileRecursive = (dir, filename) => {
              try {
                const files = fs.readdirSync(dir, { withFileTypes: true });
                for (const file of files) {
                  const fullPath = path.join(dir, file.name);
                  if (file.isDirectory()) {
                    if (['node_modules', 'public', '.git', 'build', 'dist', 'coverage'].includes(file.name)) continue;
                    const found = findFileRecursive(fullPath, filename);
                    if (found) return found;
                  } else if (file.isFile()) {
                    const fileBaseName = file.name.replace(/\.(js|jsx|ts|tsx)$/, '');
                    if (fileBaseName === filename) return fullPath;
                  }
                }
              } catch {}
              return null;
            };

            const changesByFile = {};
            changes.forEach((change) => {
              if (!changesByFile[change.fileName]) {
                changesByFile[change.fileName] = [];
              }
              changesByFile[change.fileName].push(change);
            });

            Object.entries(changesByFile).forEach(([fileName, fileChanges]) => {
              let targetFile = findFileRecursive(frontendRoot, fileName);
              if (!targetFile) {
                targetFile = path.resolve(frontendRoot, 'src/components', `${fileName}.js`);
              }

              const normalizedTarget = path.normalize(targetFile);
              const isInFrontend = normalizedTarget.startsWith(frontendRoot) && !normalizedTarget.includes('..');
              const isNodeModules = normalizedTarget.includes('node_modules');
              const isPublic = normalizedTarget.includes('/public/') || normalizedTarget.endsWith('/public');

              if (!isInFrontend || isNodeModules || isPublic) {
                throw new Error(`Forbidden path for file ${fileName}`);
              }

              if (!fs.existsSync(targetFile)) {
                throw new Error(`File not found: ${targetFile}`);
              }

              const currentContent = fs.readFileSync(targetFile, 'utf8');
              const ast = parser.parse(currentContent, {
                sourceType: 'module',
                plugins: ['jsx', 'typescript'],
              });

              const parseJsxChildren = (content) => {
                if (content === undefined) return null;
                const sanitizeMetaAttributes = (node) => {
                  if (t.isJSXElement(node)) {
                    node.openingElement.attributes = node.openingElement.attributes.filter((attr) => {
                      if (t.isJSXAttribute(attr) && t.isJSXIdentifier(attr.name)) {
                        return !attr.name.name.startsWith('x-');
                      }
                      return true;
                    });
                    node.children.forEach((child) => sanitizeMetaAttributes(child));
                  } else if (t.isJSXFragment(node)) {
                    node.children.forEach((child) => sanitizeMetaAttributes(child));
                  }
                };

                try {
                  const wrapperExpression = parser.parseExpression(`(<gjs-wrapper>${content}</gjs-wrapper>)`, {
                    sourceType: 'module',
                    plugins: ['jsx', 'typescript'],
                  });
                  if (t.isJSXElement(wrapperExpression)) {
                    const innerChildren = wrapperExpression.children || [];
                    innerChildren.forEach((child) => sanitizeMetaAttributes(child));
                    return innerChildren;
                  }
                } catch {}
                return [t.jsxText(content)];
              };

              const changesByLine = {};
              fileChanges.forEach((change) => {
                if (!changesByLine[change.lineNumber]) {
                  changesByLine[change.lineNumber] = [];
                }
                changesByLine[change.lineNumber].push(change);
              });

              traverse(ast, {
                JSXOpeningElement: (nodePath) => {
                  const lineNumber = nodePath.node.loc?.start.line;
                  if (!lineNumber) return;

                  const changesAtLine = changesByLine[lineNumber];
                  if (!changesAtLine || changesAtLine.length === 0) return;

                  const elementName = nodePath.node.name.name;

                  changesAtLine.forEach((change) => {
                    if (elementName !== change.component) return;

                    if (change.type === 'className' && change.className !== undefined) {
                      let classAttr = nodePath.node.attributes.find(
                        (attr) => t.isJSXAttribute(attr) && attr.name.name === 'className'
                      );
                      const oldClassName = classAttr?.value?.value || '';

                      if (classAttr) {
                        classAttr.value = t.stringLiteral(change.className);
                      } else {
                        const newClassAttr = t.jsxAttribute(
                          t.jsxIdentifier('className'),
                          t.stringLiteral(change.className)
                        );
                        nodePath.node.attributes.push(newClassAttr);
                      }

                      edits.push({
                        file: getRelativePath(targetFile),
                        lineNumber,
                        element: elementName,
                        type: 'className',
                        oldData: oldClassName,
                        newData: change.className,
                      });
                    } else if (change.type === 'textContent' && change.textContent !== undefined) {
                      const parentElementPath = nodePath.parentPath;
                      if (parentElementPath && parentElementPath.isJSXElement()) {
                        const jsxElementNode = parentElementPath.node;
                        const children = jsxElementNode.children || [];
                        let targetTextNode = children.find((c) => t.isJSXText(c) && c.value.trim().length > 0);
                        const newContent = change.textContent;
                        let oldContent = '';

                        const preserveWhitespace = (orig, updated) => {
                          const lead = (orig.match(/^\s*/) || [''])[0];
                          const trail = (orig.match(/\s*$/) || [''])[0];
                          return `${lead}${updated}${trail}`;
                        };

                        if (targetTextNode) {
                          oldContent = targetTextNode.value.trim();
                          targetTextNode.value = preserveWhitespace(targetTextNode.value, newContent);
                        } else {
                          const newTextNode = t.jsxText(newContent);
                          jsxElementNode.children = [newTextNode, ...children];
                        }

                        edits.push({
                          file: getRelativePath(targetFile),
                          lineNumber,
                          element: elementName,
                          type: 'textContent',
                          oldData: oldContent,
                          newData: newContent,
                        });
                      }
                    } else if (change.type === 'content' && change.content !== undefined) {
                      const parentElementPath = nodePath.parentPath;
                      if (parentElementPath && parentElementPath.isJSXElement()) {
                        const oldChildren = parentElementPath.node.children || [];
                        const oldContentAST = { type: 'JSXFragment', children: oldChildren };
                        const oldContent = generate(oldContentAST, {}, '').code.replace(/^<>/, '').replace(/<\/>$/, '').trim();

                        const newChildren = parseJsxChildren(change.content);
                        if (newChildren) {
                          parentElementPath.node.children = newChildren;
                        }

                        edits.push({
                          file: getRelativePath(targetFile),
                          lineNumber,
                          element: elementName,
                          type: 'content',
                          oldData: oldContent,
                          newData: change.content,
                        });
                      }
                    } else {
                      rejectedChanges.push({
                        change,
                        reason: `Invalid change type: ${change.type}`,
                        file: getRelativePath(targetFile),
                        lineNumber,
                        element: elementName,
                      });
                    }
                  });

                  delete changesByLine[lineNumber];
                },
              });

              const { code } = generate(ast, {
                retainLines: true,
                retainFunctionParens: true,
                comments: true,
              });

              fs.writeFileSync(targetFile, code, 'utf8');

              try {
                execSync(`git -c user.name="visual-edit" -c user.email="support@emergent.sh" add "${targetFile}"`);
                execSync(`git -c user.name="visual-edit" -c user.email="support@emergent.sh" commit -m "visual_edit_${Date.now()}"`);
              } catch {}
            });

            const response = { status: 'ok', edits };
            if (rejectedChanges.length > 0) {
              response.rejectedChanges = rejectedChanges;
            }

            res.statusCode = 200;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify(response));
          } catch (err) {
            res.statusCode = 500;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ error: err.message }));
          }
        });
      });
    },
  };
}

export default defineConfig({
  plugins: [
    react(),
    visualEditsPlugin(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    extensions: ['.mjs', '.js', '.mts', '.ts', '.jsx', '.tsx', '.json'],
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
  },
  esbuild: {
    loader: 'jsx',
    include: /src\/.*\.jsx?$/,
    exclude: [],
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    strictPort: true,
    allowedHosts: [
      'tape-erp.preview.emergentagent.com',
      '.emergentagent.com',
      '.emergent.sh',
      '.emergentcf.cloud',
      'localhost',
      'adhesive-powerhouse.cluster-6.preview.emergentcf.cloud',
      'erp-adhesive-hub.preview.emergentagent.com',
      'erp-adhesive-hub.cluster-0.preview.emergentcf.cloud',
    ],
    watch: {
      ignored: ['**/node_modules/**', '**/.git/**', '**/build/**', '**/dist/**', '**/coverage/**'],
    },
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  },
  define: {
    'process.env': {},
  },
});
