# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Exceptions to be used by Aquilon"""
"""The base exception class is AquilonError."""

def deprecated(message):
    import warnings
    warnings.warn(message, DeprecationWarning, stacklevel=2)


class AquilonError(StandardError):
    '''Generic error class.'''


class ArgumentError(AquilonError):
    """Raised for all those conditions where invalid arguments are
    sent to constructed objects.  This error generally corresponds to
    construction time state errors.

    """


class ProtocolError(AquilonError):
    """Raised when an import of a protocol fails

    """


class ProcessException(AquilonError):
    """Raised when a process being executed fails."""
    def __init__(self, command=None, out=None, err=None,
            code=None, signalNum=None):
        self.command = command
        self.out = out
        self.err = err
        self.code = code
        self.signalNum = signalNum
        if command:
            msg = "Command '%s' failed" % command
        else:
            msg = "Command failed"
        if code:
            msg = msg + " with return code '%d'" % code
        elif signalNum:
            msg = msg + " with signal '%d'" % signalNum
        if err and err.strip():
            msg = msg + " and stderr:\n%s" % err
        elif out and out.strip():
            msg = msg + " and stdout:\n%s" % out
        StandardError.__init__(self, msg)


class RollbackException(AquilonError):
    """If this is being thrown, should attempt to rollback any high-level
    activities being executed."""
    # This isn't fully baked yet... might not be necessary.
    def __init__(self, jobid=None, cause=None, *args, **kwargs):
        self.jobid = jobid
        self.cause = cause
        if not args and cause:
            args = [ str(cause) ]
        AquilonError.__init__(self, *args, **kwargs)


class AuthorizationException(AquilonError):
    """Raised when a principle is not authorized to perform a given
    action on a resource.

    """


class NotFoundException(AquilonError):
    """Raised when a requested resource cannot be found."""


class NameServiceError(AquilonError):
    """Raised when a host or service name cannot be found, or differs from,
    what's stored in name services such as dns."""


class UnimplementedError(AquilonError):
    """Raised when a command has not been implemented."""


class IncompleteError(AquilonError):
    """Raised when an incomplete/unusable template would be generated."""


class DetailedProcessException(AquilonError):
    """Raised when more details about a process exception should
    be shown to the client.

    """

    def __init__(self, pe, input=None, output=None):
        self.processException = pe
        self.output = output
        msg = str(pe) + "\n"
        if input:
            msg = msg + "\ninput:\n" + input + "\n"
        if output:
            msg = msg + "\nstdout:\n" + output + "\n"
        elif pe.out:
            msg = msg + "\nstdout:\n" + pe.out + "\n"
        if pe.err:
            msg = msg + "\nstderr:\n" + pe.err + "\n"
        AquilonError.__init__(self, msg)


class PartialError(AquilonError):
    """Raised when a batch job has some failures."""

    def __init__(self, success, failed, success_msg=None, failed_msg=None):
        msg = []
        if success_msg:
            msg.append(success_msg)
        else:
            msg.append("The following were successful:")
        msg.extend(success)
        if failed_msg:
            msg.append(failed_msg)
        else:
            msg.append("The following failed:")
        msg.extend(failed)
        AquilonError.__init__(self, "\n".join(msg))


