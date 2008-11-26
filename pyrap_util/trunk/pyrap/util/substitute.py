# substitute.py: substitute glish variables and expressions
# Copyright (C) 1998,1999,2008
# Associated Universities, Inc. Washington DC, USA.
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Library General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Library General Public
# License for more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 675 Massachusetts Ave, Cambridge, MA 02139, USA.
#
# Correspondence concerning AIPS++ should be addressed as follows:
#        Internet email: aips2-request@nrao.edu.
#        Postal address: AIPS++ Project Office
#                        National Radio Astronomy Observatory
#                        520 Edgemont Road
#                        Charlottesville, VA 22903-2475 USA
#
# $Id$


# This function tries to substitute $name by its value.
# The following rules apply:
# 1. A name must start with an underscore or alphabetic, followed
#    by zero or more alphanumerics and underscores.
# 2. Parts enclosed in single or double quotes are left untouched.
#    Furthermore a $ can be escaped by a backslash, which is useful
#    if an environment variable is used. Note that glish
#    requires an extra backslash to escape the backslash.
#    The output contains the quotes and backslashes.
# 3. If name has a vector value, its substitution is enclosed in
#    square brackets and separated by commas.
# 4. A string value is enclosed in double quotes. If the value
#    contains a double quote, that quote is enclosed in single quotes.
# 5. If the name's value has a type mentioned in the objlist, it is
#    substituted by $n (n is a sequence number) and its value is added to the
#    objects of that type.
# 6. If the name is unknown or has an unknown type, it is left untouched
#    (thus the result contains $name).
#
# The objlist argument is a list of sequences where each sequence has
# three fields:
# 1. The first field is the object type (e.g. table)
# 2. The second field is a prefix for the sequence number
#    E.g. regions could have prefix 'r' resulting in $r1.
# 3. The third field is a list of objects to be substituted. New objects
#    get appended to it.

# Furthermore it substitutes $(expression) by the expression result.
# It correctly handles parentheses and quotes in the expression.
# E.g.   $(a+b)
#        $((a+b)*(a+b))
#        $(len("ab cd( de"))
# Similar escape rules as above apply.
#
# Substitution is NOT recursive. E.g. if a=1 and b="$a",
# the result of substitute("$a") is "$a" and not 1.

def getglobals():
    """Get the global variables"""
    import inspect
    fr = inspect.currentframe()
    try:
        while fr:
            fr1 = fr;
            fr  = fr.f_back
    except:
        pass
    return fr1.f_locals


def substitute (s, objlist=()):
  # Get the symbols at the desired level.
  symcp = getglobals()
  # Split the string into its individual characters.
  # Initialize some variables.
  backslash = False
  dollar = False
  nparen = 0
  name = ''
  evalstr = ''
  squote = False
  dquote = False
  out = ''
  # Loop through the entire string.
  for tmp in s:
# If a dollar was found, we might have a name.
# Alphabetics and underscore are always part of name.
    if dollar:
      if tmp=='_'  or  (tmp>='a' and tmp<='z')  or  (tmp>='A' and tmp<='Z'):
        name += tmp
        tmp = ''
      else:
# Numerics are only part if not first character.
        if tmp>='0' and tmp<='9' and name!='':
          name += tmp
          tmp = ''
        else:
          if tmp=='(' and name=='':
# $( indicates the start of a subexpression to evaluate.
            nparen = 1
            evalstr = ''
            tmp = ''
            dollar = False
          else:
# End of name found. Try to substitute.
            dollar = False
            out += substitutename(name, objlist, symcp)

    if tmp != '':
# Handle possible single or double quotes.
      if tmp == '"'  and  not squote:
        dquote = not dquote
      else:
        if tmp == "'"  and  not dquote:
          squote = not squote
        else:
          if not dquote and not squote:
# Count the number of balanced parentheses (outside quoted strings)
# in the subexpression.
            if nparen > 0:
              if tmp == '(':
                nparen += 1
              else:
                if tmp == ')':
                  nparen -= 1
                  if nparen == 0:
# The last closing parenthese is found.
# Evaluate the subexpression and if successful put the result in the output.
                    out += substituteexpr(evalstr, symcp)
                    tmp = ''
            else:
# Set a switch if we have a dollar (outside quoted and eval strings)
# that is not preceeded by a backslash.
              if tmp == '$'  and  not backslash:
                dollar = True
                name = ''
                tmp = ''
# Add the character to output or eval string.
# Set a switch if we have a backslash.
    if tmp != '':
      if nparen > 0:
        evalstr += tmp
      else:
        out += tmp
    backslash = (tmp == '\\')

# The entire string has been handled.
# Substitute a possible last name.
# Insert a possible incomplete eval string as such.
  if dollar:
    out += substitutename(name, objlist, symcp)
  else:
    if nparen > 0:
      out += '$(' + evalstr
  return out




# This function tries to substitute the given name using
# the rules described in the description of function substitute.
def substitutename (name, objlist, symcp):

# If the name is empty, return a single dollar.
  if len(name) == 0:
    return '$'

# If the name is undefined, return the original.
  try:
    v = eval(name, symcp, symcp)
  except NameError:
    return '$' + name

# See if the resulting value is one of the given special types.
  try:
    for objtype,objstr,objs in objlist:
      if isinstance(v, objtype):
        objs += [v]
        return '$' + objstr + str(len(objs))
  except:
    pass

# No specific type, thus a normal value has to be substituted.
  return substitutevar(v)




# This function tries to substitute the given name using
# the rules described in the description of function substitute.
def substituteexpr (expr, symcp={}):
  try:
    res = eval(expr, symcp, symcp)
    v = substitutevar(res)
  except:
# If the expr is undefined, return the original.
    v = '$(' + expr + ')'
  return str(v)



# Substitute a value.
def substitutevar (v):
  out=''
  if isinstance (v, tuple)  or  isinstance (v, list):
    out = '['
    first = True
    for tmp in v:
      if first:
        first = False
      else:
        out += ','
      out += substituteonevar(tmp)
    out += ']'
  else:
    out = substituteonevar(v)
  return out


def substituteonevar (v):
# A string needs to be enclosed in quotes.
# A vector value is enclosed in square brackets and separated by commas.
  if isinstance (v, str):
    return substitutestring (v)
# A numeric or boolean value is converted to a string.
# A vector value is enclosed in square brackets and separated by commas.
# Take care we have enough precision.
  if isinstance (v, bool):
    if v:
      return 'T'
    return 'F'
  return str(v)



# Enclose a string in double quotes.
# If the string contains double quotes, enclose them in single quotes.
# E.g.             ab"cd
# is returned as   "ab"'"'"cd"
# which is according to the TaQL rules for strings.
def substitutestring (value):
  out='"'
  for tmp in value:
    if tmp == '"':
      out += '"' + "'" + '"' + "'" + '"'
    else:
      out += tmp
  return out + '"'
