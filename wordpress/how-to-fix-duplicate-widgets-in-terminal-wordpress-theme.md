# How to Fix Duplicate Widgets in Terminal WordPress Theme

If you are using the Terminal theme for WordPress and you've noticed that your widgets are appearing twice in your sidebar or footer, you're not alone. This is a common issue that can happen due to a few different reasons, especially after WordPress core updates or theme migrations.

Here is a quick guide on how to troubleshoot and fix duplicate widgets in the Terminal WordPress theme.

## 1. The Classic Widgets Fix (Most Common)

Since WordPress 5.8, the classic widget editor was replaced with a block-based widget editor. While this is great for modern themes, older themes like Terminal might not fully support it, causing widgets to duplicate or render incorrectly.

**Solution:**
The easiest way to fix this is to restore the classic widgets screen.
1. Go to your WordPress Dashboard.
2. Navigate to **Plugins > Add New**.
3. Search for **Classic Widgets** (it is an official plugin maintained by the WordPress core team).
4. Install and activate the plugin.
5. Go back to **Appearance > Widgets** and check if the duplicates are gone.

## 2. Clear Inactive Widgets

Sometimes, when you switch themes or update, widgets get moved around and duplicated in the background.

**Solution:**
1. Go to **Appearance > Widgets**.
2. Scroll down to the **Inactive Widgets** section.
3. If you see a lot of widgets piled up here, hit the **Clear Inactive Widgets** button.
4. Refresh your site to see if the issue is resolved.

## 3. Check for Duplicate Registrations in `functions.php`

If you have customized your Terminal theme's `functions.php` file, you might have accidentally registered the same sidebar or widget area twice.

**Solution:**
1. Go to **Appearance > Theme File Editor**.
2. Select your `functions.php` file.
3. Search for the `register_sidebar()` function.
4. Ensure that each sidebar has a unique `id` and is only registered once.

```php
// Example of a correct registration
function terminal_widgets_init() {
    register_sidebar( array(
        'name'          => __( 'Sidebar', 'terminal' ),
        'id'            => 'sidebar-1',
        'description'   => __( 'Add widgets here.', 'terminal' ),
        'before_widget' => '<section id="%1$s" class="widget %2$s">',
        'after_widget'  => '</section>',
        'before_title'  => '<h2 class="widget-title">',
        'after_title'   => '</h2>',
    ) );
}
add_action( 'widgets_init', 'terminal_widgets_init' );
```

## 4. Clear Your Cache

If you are using a caching plugin (like LiteSpeed Cache, W3 Total Cache, or WP Super Cache), your site might be serving an old, bugged version of the page.

**Solution:**
Simply purge or clear all caches from your caching plugin's settings, and clear your browser cache before checking the site again.

---
Hopefully, one of these solutions helped you get your Terminal theme looking clean and functional again!
