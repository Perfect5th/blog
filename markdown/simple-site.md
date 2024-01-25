# Simple Site

## 2024-01-22

A couple days ago, my friend [tendermario][1] sent me a message:

> I honestly want to make a md file sorta layout that gets converted into html and just static serve
> on github pages

Now I know there are a lot of ways to accomplish this, but _I_ didn't create any of those, so by
the doctrine of not-invented-here, I made [Simple Site][2]. The name probably already clashes with
something existing, and I'm open to changing it as soon as a better idea comes along.

The main concept was to see if I could produce a static site generator in less than 100 lines of
shell script. Obviously there is some cheating involved: it uses [markdown][3] to produce the actual
html that is inserted into the html files, but I've built a few niceties around that, and it comes
with a GitHub workflow that publishes it to GitHub Pages.

Here's a non-exhaustive feature list:

 - configurable `SITE_ROOT` if you want to host it at different URLs
 - optional navigation breadcrumbs
 - support for a single CSS file, a single JS file, and font files
 - generated titles for pages (from first-line `h1` of markdown file)
 
That's about it, for now. I don't think I'll add much more. The site you're currently reading this
on was generated using this project. Maybe I'll add a footer.

Using it is very simple, and that's kind of the point. The `README` might explain it more but here's
the gist:

 1. Clone the repo
 1. Write whatever CSS you want or need in `./css/base.css`
 1. Write whatever content you want in `./markdown/` (make sure to include) `index.md` files if you
    want `index.html` files in each directory.
 1. Write whatever JS you want or need in `./js/main.js`
 1. Add whatever font files you need to `./fonts/`
 1. Edit `./env` to set `SITE_ROOT`, `SITE_TITLE`, and `CRUMBS`
 1. Install `markdown`
 1. Run `./convert.sh`
 1. Serve your resulting `./_site/` from wherever you feel like
 
When I test it locally I do this:

 1. `SITE_ROOT="/" ./convert.sh`
 1. `cd ./_site/ && python3 -m http.server`
 
Oh, and it's GPLv3 licensed, so feel free to do with that what you will.

— Mitch

   [1]: https://github.com/tendermario "tendermario's GitHub"
   [2]: https://github.com/Perfect5th/simple-site/ "Simple Site GitHub Repository"
   [3]: https://daringfireball.net/projects/markdown/ "Daring Fireball's Markdown Project Page"
